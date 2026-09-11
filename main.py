import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import gemini_engine
import pilot_data
import stt_engine

BASE = Path(__file__).parent
app = FastAPI(title="Kaalaman at Karapatan")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


MOODS = ["neutral", "kabado", "malungkot", "ginhawa"]
# Ang mga art file sa disk ay Ingles ang pangalan (nervous/sad/relieved);
# dito ibinabagay sa Tagalog na mood key na ginagamit ng laro.
MOOD_FILE = {"neutral": "neutral", "kabado": "nervous", "malungkot": "sad", "ginhawa": "relieved"}
ART_DIR = BASE / "static" / "art"


def load_cases():
    with open(BASE / "game_data" / "cases.json", encoding="utf-8") as f:
        return json.load(f)["cases"]


def art_inventory():
    """Bawat art key na ginagamit sa cases.json, kasama kung anong mood ang may file."""
    used = {}
    for c in load_cases():
        key = (c.get("bata") or {}).get("art")
        if key:
            used.setdefault(key, []).append(c.get("title") or c.get("id", ""))
    return [
        {
            "key": key,
            "cases": titles,
            "moods": [{"mood": m, "exists": (ART_DIR / f"{key}_{MOOD_FILE.get(m, m)}.png").exists()}
                      for m in MOODS],
        }
        for key, titles in sorted(used.items())
    ]


@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse(request, "welcome.html")


@app.get("/menu", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active": "home"})


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"active": "chat"})


@app.get("/mga-kuwento")
def stories_redirect():
    return RedirectResponse("/laro")


@app.get("/laro", response_class=HTMLResponse)
def laro(request: Request):
    ready = [c for c in load_cases() if c.get("status") == "ready"]
    cases_json = json.dumps(ready, ensure_ascii=False)
    return templates.TemplateResponse(request, "booth.html", {"cases_json": cases_json})


@app.get("/laro/art", response_class=HTMLResponse)
def art_check(request: Request):
    rows = art_inventory()
    total = sum(len(r["moods"]) for r in rows)
    have = sum(1 for r in rows for m in r["moods"] if m["exists"])
    return templates.TemplateResponse(
        request, "art_check.html",
        {"rows": rows, "total": total, "have": have, "missing": total - have},
    )


class HistoryTurn(BaseModel):
    who: str
    text: str


class ChatMessage(BaseModel):
    message: str
    # Huling ilang turn ng PAREHONG session, ipinapadala ng frontend (tingnan
    # ang chatLog sa static/script.js, na naka-persist na sa sessionStorage).
    # Walang server-side session/database sa proyektong ito, kaya ang
    # client mismo ang may hawak ng "memorya" -- opsyonal ito para hindi
    # masira ang lumang behavior kung walang ipinadalang history.
    history: Optional[list[HistoryTurn]] = None


# Bantay laban sa duplicate/sabay-sabay na request (hal. kapag na-double
# click ang Send, o may bagong tab na nag-resubmit ng parehong mensahe habang
# hinihintay pa ang una). Ang frontend (static/script.js) mismo ang unang
# linya ng depensa -- naka-disable ang input/buttons habang may request pa
# -- pero dahil walang totoong server-side session/lock sa proyektong ito,
# ito ang backup: kung EXACT parehong mensahe ang dumating ulit sa loob ng
# ilang segundo (na malamang ay double-submit lang, hindi bagong tanong ng
# user), ibabalik na lang ang parehong ligtas na paalala sa halip na
# muling patakbuhin (at gastusin) ang buong Gemini call. Hindi ito
# per-session/per-user (in-memory, process-wide) dahil walang session id
# na ipinapasa ng frontend -- sapat na ito para sa layuning ito (iwasan
# ang aksidenteng dobleng klik), hindi ito panlaban sa sadyang pag-atake.
_RECENT_REQUESTS: dict[str, float] = {}
_DUPLICATE_WINDOW_SECONDS = 4.0


def _is_recent_duplicate(text: str) -> bool:
    now = time.monotonic()
    # Linisin muna ang mga lumang entry para hindi lumaki nang walang hanggan.
    stale = [k for k, ts in _RECENT_REQUESTS.items() if now - ts > _DUPLICATE_WINDOW_SECONDS]
    for k in stale:
        _RECENT_REQUESTS.pop(k, None)
    last = _RECENT_REQUESTS.get(text)
    _RECENT_REQUESTS[text] = now
    return last is not None and (now - last) < _DUPLICATE_WINDOW_SECONDS


@app.post("/api/chat")
def chat_api(payload: ChatMessage):
    text = payload.message.strip()
    if not text:
        return {"reply": "Pakisulat po ang tanong ninyo."}
    if _is_recent_duplicate(text):
        return {
            "reply": "Natanggap na po ang tanong ninyo -- pakihintay lang ang sagot dito. "
                     "(Received your question already -- please wait for the reply.)",
            "citations": [],
        }
    history = [t.model_dump() for t in payload.history] if payload.history else None
    # gemini_engine.respond() ang bahalang mag-desisyon: gamitin si Gemini
    # (RAG-grounded sa RA 9344/10630/IRR) kung may API key at gumagana ang
    # koneksyon, o bumalik sa offline na intent_engine.py kapag wala/nag-error.
    # Ang history ay ginagamit lang bilang CONTEXT para sa follow-up na mga
    # tanong -- hindi ito bagong sanggunian ng batas (tingnan ang paliwanag
    # sa gemini_engine.py).
    return gemini_engine.respond(text, history=history)


# ============================================================
# SOP1: TAGLISH SPEECH-TO-TEXT (Whisper-small) -- /api/stt
# ============================================================
# Ang aktwal na modelo (stt_engine.py) ay hiwalay dating na-validate na sa
# mga script na test_whisper.py/baseline_wer.py, pero hindi pa dati
# isinasama sa totoong web app -- ang mic button sa chat ay placeholder
# lamang dati ("Speech input is still in progress"). Dito na ito unang
# ikinabit: kinukuha ang raw na audio mula sa browser (MediaRecorder,
# karaniwang webm/opus), kino-convert sa 16kHz mono WAV via ffmpeg
# (parehong hakbang gaya ng convert_audio.py), tapos ipinapasa kay
# stt_engine.transcribe(). Ang na-transcribe na teksto ay ibinabalik sa
# frontend PARA LANG ILAGAY SA INPUT BOX (hindi direktang ipinapadala
# bilang chat message) -- sinasadya ito, para may pagkakataon ang user na
# suriin/ayusin ang teksto bago ito ipadala, dahil hindi 100% tama lagi
# ang STT lalo na sa code-switched/Taglish speech.
MAX_AUDIO_BYTES = 15 * 1024 * 1024  # ~15MB -- sapat na para sa maikling tanong ng bata
FFMPEG_TIMEOUT_SECONDS = 30


def _convert_to_wav(raw: bytes, tmp_dir: str) -> Optional[str]:
    """
    Kino-convert ang raw na audio bytes (karaniwang webm/opus mula sa
    browser MediaRecorder) sa 16kHz mono WAV via ffmpeg -- parehong
    hakbang na ginagamit na ng convert_audio.py para sa training data.
    Ibinabalik ang path ng na-convert na WAV, o None kapag nabigo.
    Ginagamit ito ng /api/stt AT /api/pilot/save, para hindi maulit ang
    parehong logic sa dalawang lugar.
    """
    in_path = os.path.join(tmp_dir, "input")
    out_path = os.path.join(tmp_dir, "converted.wav")
    with open(in_path, "wb") as f:
        f.write(raw)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", out_path],
            check=True, capture_output=True, timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None
    return out_path


@app.post("/api/stt")
async def stt_api(audio: UploadFile = File(...)):
    raw = await audio.read()
    if not raw:
        return {"error": "Walang natanggap na audio."}
    if len(raw) > MAX_AUDIO_BYTES:
        return {"error": "Masyadong mahaba ang audio. Subukan ang mas maikling tanong."}
    if shutil.which("ffmpeg") is None:
        return {"error": "Hindi available ang ffmpeg sa server na ito. I-type na lang muna ang tanong."}

    with tempfile.TemporaryDirectory() as tmp:
        out_path = _convert_to_wav(raw, tmp)
        if out_path is None:
            return {"error": "Hindi ma-convert ang audio (posibleng sirang recording). Subukan ulit."}
        return stt_engine.transcribe(out_path)


# ============================================================
# OPSYONAL NA "PILOT MODE" -- /api/pilot/consent, /api/pilot/save
# ============================================================
# Tingnan ang pilot_data.py para sa buong paliwanag. Buod: naka-OFF ito
# bilang default. Kapag tahasang pinagana ng user sa UI (matapos munang
# mag-agree sa isang consent screen -- tingnan ang static/script.js --
# na kumpirmasyon na 18+ siya at proxy speaker lang, hindi aktwal na CICL
# na bata), ang mga audio na nire-record niya sa mismong mic button ng
# chat, kasama ang FINAL na tekstong aktwal niyang ipinadala, ay
# maaaring i-save bilang bagong (audio, corrected-text) na training
# pair para sa SOP1 fine-tuning -- hiwalay na folder (pilot_data/) muna,
# hindi direktang idinaragdag sa training set, para may pagkakataong
# i-review muna bago isama.
@app.post("/api/pilot/consent")
async def pilot_consent(session_id: str = Form(...)):
    pilot_data.log_consent(session_id)
    return {"ok": True}


@app.post("/api/pilot/save")
async def pilot_save(
    audio: UploadFile = File(...),
    text: str = Form(...),
    session_id: str = Form(...),
    consented: bool = Form(...),
):
    # Karagdagang safeguard sa server side (bukod sa gate na nasa UI) --
    # tinatanggihan ang kahit anong save request na walang tahasang
    # `consented=True` na kasama, kahit paano ito nangyari.
    if not consented:
        return {"error": "Walang consent -- hindi na-save."}
    clean_text = (text or "").strip()
    if not clean_text:
        return {"error": "Walang text, hindi na-save."}
    raw = await audio.read()
    if not raw:
        return {"error": "Walang audio, hindi na-save."}
    if len(raw) > MAX_AUDIO_BYTES:
        return {"error": "Masyadong mahaba ang audio, hindi na-save."}
    if shutil.which("ffmpeg") is None:
        return {"error": "Hindi available ang ffmpeg, hindi na-save."}

    with tempfile.TemporaryDirectory() as tmp:
        out_path = _convert_to_wav(raw, tmp)
        if out_path is None:
            return {"error": "Hindi ma-convert ang audio, hindi na-save."}
        wav_bytes = Path(out_path).read_bytes()

    file_name = pilot_data.save_pair(session_id, wav_bytes, clean_text)
    return {"saved": True, "file_name": file_name}

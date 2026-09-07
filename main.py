import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import gemini_engine

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


@app.post("/api/chat")
def chat_api(payload: ChatMessage):
    text = payload.message.strip()
    if not text:
        return {"reply": "Pakisulat po ang tanong ninyo."}
    history = [t.model_dump() for t in payload.history] if payload.history else None
    # gemini_engine.respond() ang bahalang mag-desisyon: gamitin si Gemini
    # (RAG-grounded sa RA 9344/10630/IRR) kung may API key at gumagana ang
    # koneksyon, o bumalik sa offline na intent_engine.py kapag wala/nag-error.
    # Ang history ay ginagamit lang bilang CONTEXT para sa follow-up na mga
    # tanong -- hindi ito bagong sanggunian ng batas (tingnan ang paliwanag
    # sa gemini_engine.py).
    return gemini_engine.respond(text, history=history)

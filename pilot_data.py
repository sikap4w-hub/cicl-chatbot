"""
pilot_data.py
-------------
Opsyonal na "Pilot Mode" para sa live chat app: kapag tahasang pumayag
(consent) ang isang CONSENTING ADULT proxy speaker, ang mga audio na
nire-record niya sa pamamagitan ng aktwal na mic button sa chat ay
maaaring i-save bilang bagong STT TRAINING PAIR -- ang audio, kasama ang
FINAL na tekstong AKTWAL niyang ipinadala bilang mensahe (pagkatapos
niyang baguhin/kumpirmahin ang unang hula ng Whisper). Ito ang totoong
"ground truth" label, HINDI ang unang output ng speech-to-text.

MAHALAGA -- sinusunod nito ang parehong alituntunin ng buong proyekto:
lahat ng speech training data ay dapat galing sa CONSENTING ADULT PROXY
speakers, hindi sa aktwal na batang gumagamit ng deployed system. Kaya:
  - Naka-OFF ito bilang default -- walang kahit anong audio ang na-save
    maliban kung tahasang na-activate ang Pilot Mode sa UI (tingnan ang
    static/script.js), na nangangailangan munang mag-agree sa isang
    consent screen (kumpirmasyon na 18+ ang gumagamit at proxy speaker
    lang, hindi aktwal na CICL na bata).
  - Bawat save ay may kasamang `consented=True` flag mula sa client --
    tinatanggihan ng /api/pilot/save endpoint (main.py) ang kahit anong
    request na walang ganitong flag, bilang karagdagang safeguard.
  - Walang PII na kinukuha -- random, hindi-PII na session id lang ang
    naka-attach sa bawat clip (hindi pangalan/email/IP/atbp.), consistent
    sa "anonymous, session-based" na disenyo ng buong app.
  - Ang mga na-save na file dito ay HINDI otomatikong idinaragdag sa
    training set -- pinananatili itong hiwalay na folder (pilot_data/)
    para may pagkakataong i-REVIEW muna (adviser/research team) bago
    isama sa dataset, gaya ng ipinaliwanag sa consent text mismo.
"""
import csv
import json
import time
import uuid
from pathlib import Path

BASE = Path(__file__).parent
PILOT_DIR = BASE / "pilot_data"
PILOT_AUDIO_DIR = PILOT_DIR / "audio"
PILOT_METADATA_PATH = PILOT_DIR / "metadata.csv"
PILOT_CONSENT_LOG_PATH = PILOT_DIR / "consent_log.jsonl"

_METADATA_FIELDS = ["file_name", "transcription"]


def _ensure_dirs():
    PILOT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def log_consent(session_id: str):
    """
    Nagtatala LANG na may nagbigay ng consent sa isang partikular na
    (random, hindi-PII) na session id, kasama ang timestamp -- para lang
    magkaroon ng audit trail kung ilang session ang talagang pumayag,
    sakaling kailanganin ito ng adviser/ethics review. Walang ibang
    detalye ang naka-log dito.
    """
    _ensure_dirs()
    entry = {"session_id": session_id, "consented_at": time.time()}
    with open(PILOT_CONSENT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def save_pair(session_id: str, wav_bytes: bytes, final_text: str) -> str:
    """
    Sine-save ang isang (audio, corrected-text) pair sa pilot_data/.
    Ang `final_text` ay dapat ang tekstong AKTWAL na ipinadala ng user
    pagkatapos niyang baguhin/kumpirmahin ang STT guess sa input box --
    ito ang ground-truth label. Ginagamit ang parehong CSV schema
    (file_name, transcription) gaya ng data/metadata.csv na ginagamit na
    ng baseline_wer.py/fine-tuning script, para madali itong maisama sa
    training set (kopyahin lang ang mga .wav papunta sa data/, at i-merge
    ang metadata.csv) kapag na-review na at inaprubahan.
    """
    _ensure_dirs()
    clip_id = f"pilot_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    file_name = f"{clip_id}.wav"
    (PILOT_AUDIO_DIR / file_name).write_bytes(wav_bytes)

    is_new = not PILOT_METADATA_PATH.exists()
    with open(PILOT_METADATA_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_METADATA_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({"file_name": file_name, "transcription": final_text})
    return file_name

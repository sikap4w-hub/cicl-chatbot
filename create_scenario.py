import os

# ============================================================
# Screen 5 (Scenario) at Screen 6 (Consequence).
# Binabasa ang laman mula sa game_data/storyboards.json.
# Patakbuhin: python create_scenario.py
# ============================================================

os.makedirs("templates", exist_ok=True)

# ------------------------------------------------------------
# main.py  (idinagdag ang scenario at consequence routes)
# ------------------------------------------------------------
main_py = '''import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE = Path(__file__).parent
app = FastAPI(title="Kaalaman at Karapatan")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def load_storyboards():
    with open(BASE / "game_data" / "storyboards.json", encoding="utf-8") as f:
        return json.load(f)["storyboards"]


def get_story(sid):
    for s in load_storyboards():
        if s["id"] == sid:
            return s
    return None


@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse(request, "welcome.html")


@app.get("/menu", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active": "home"})


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"active": "chat"})


@app.get("/mga-kuwento", response_class=HTMLResponse)
def stories_page(request: Request):
    return templates.TemplateResponse(request, "game_menu.html", {"active": "game", "storyboards": load_storyboards()})


# ---------- Screen 5: Scenario ----------
@app.get("/kuwento/{sid}", response_class=HTMLResponse)
def scenario_page(request: Request, sid: str):
    story = get_story(sid)
    if not story or story.get("status") != "ready":
        return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Ginagawa pa ang kuwentong ito"})
    scene = story["scenes"][0]
    return templates.TemplateResponse(request, "scenario.html", {"active": "game", "story": story, "scene": scene})


# ---------- Screen 6: Consequence ----------
@app.get("/kuwento/{sid}/resulta/{choice}", response_class=HTMLResponse)
def consequence_page(request: Request, sid: str, choice: str):
    story = get_story(sid)
    if not story or story.get("status") != "ready":
        return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Ginagawa pa ang kuwentong ito"})
    scene = story["scenes"][0]
    # Hanapin ang pinili at ang kaugnay na consequence
    chosen = None
    for c in scene["choices"]:
        if c["id"] == choice:
            chosen = c
    if not chosen:
        return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Walang ganitong pagpipilian"})
    consequence = story["consequences"][chosen["consequence"]]
    return templates.TemplateResponse(request, "consequence.html", {
        "active": "game", "story": story, "consequence": consequence, "choice": choice
    })


class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
def chat_api(payload: ChatMessage):
    text = payload.message.strip()
    low = text.lower()
    if not text:
        return {"reply": "Pakisulat po ang tanong ninyo."}
    if "ra 9344" in low or "9344" in low:
        return {"reply": "Ang RA 9344 po ay ang Juvenile Justice and Welfare Act, na nagbibigay-proteksyon sa mga batang nasasangkot sa batas."}
    if "diversion" in low:
        return {"reply": "Ang diversion po ay alternatibong proseso na hindi dumadaan agad sa korte."}
    if "intervention" in low:
        return {"reply": "Ang intervention program po ay tulong para matutunan ng bata ang tamang gawi at makabalik sa komunidad."}
    if "tumahimik" in low or "karapatan" in low or "rights" in low:
        return {"reply": "May karapatan po kayong tumahimik at magkaroon ng magulang o social worker sa tabi ninyo."}
    if "makakatulong" in low or "sino" in low:
        return {"reply": "Maaaring tumulong sa inyo ang social worker, barangay official, o abogado."}
    return {"reply": "Naitala ko po ang tanong ninyo. (Placeholder muna ang sagot.)"}
'''

# ------------------------------------------------------------
# templates/scenario.html  (Screen 5)
# ------------------------------------------------------------
scenario_html = '''{% extends "base.html" %}
{% block content %}
<div class="chat-header">
  <a href="/mga-kuwento" class="back-btn">&larr;</a>
  <div>
    <div class="chat-title">{{ story.title }}</div>
    <div class="chat-status">Bahagi {{ scene.panel }} of {{ scene.total }}</div>
  </div>
</div>

<div class="scenario-grid">
  <div class="panel-box">
    <div class="panel-tag">PANEL {{ scene.panel }}</div>
    <div class="panel-illus">
      <svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="#f2651a" stroke-width="1.6"><rect x="3" y="8" width="18" height="9" rx="4.5"/><path d="M8 12v3M6.5 13.5h3" stroke-linecap="round"/></svg>
      <div class="illus-tag">STORY ILLUSTRATION</div>
      <div class="illus-note">{{ scene.illustration }}</div>
    </div>
    <p class="scene-text">{{ scene.text }}</p>
  </div>

  <div class="choice-box">
    <h2 class="choice-title">{{ scene.question }}</h2>
    {% for c in scene.choices %}
    <a href="/kuwento/{{ story.id }}/resulta/{{ c.id }}" class="choice">
      <span class="choice-letter">{{ c.id }}</span>
      <span>{{ c.text }}</span>
    </a>
    {% endfor %}
    <p class="choice-note">&#9432; Walang tama o maling sagot na binibilang. Layunin ay matuto.</p>
  </div>
</div>
{% endblock %}
'''

# ------------------------------------------------------------
# templates/consequence.html  (Screen 6)
# ------------------------------------------------------------
consequence_html = '''{% extends "base.html" %}
{% block content %}
<div class="chat-header">
  <a href="/kuwento/{{ story.id }}" class="back-btn">&larr;</a>
  <div>
    <div class="chat-title">Ano ang Maaaring Mangyari?</div>
    <div class="chat-status">{{ story.title }} &middot; Pinili: {{ choice }}</div>
  </div>
</div>

<div class="result-badge">&#9432; Pang-edukasyon na resulta</div>

<div class="result-box">
  <p class="result-text">{{ consequence.result }}</p>
</div>

<div class="tandaan-box">
  <div class="tandaan-title">&#128737; Mahalagang Tandaan</div>
  <p>{{ consequence.tandaan }}</p>
</div>

<div class="result-actions">
  <a href="/kuwento/{{ story.id }}/tapos" class="btn btn--blue">Magpatuloy &rsaquo;</a>
  <a href="/kuwento/{{ story.id }}" class="btn btn--ghost">Ulitin ang Choice</a>
</div>
{% endblock %}
'''

# ------------------------------------------------------------
# static/style.css  (idagdag ang scenario + consequence CSS)
# ------------------------------------------------------------
style_css = open("static/style.css", encoding="utf-8").read()

extra_css = '''

/* ---------- Scenario (Screen 5) ---------- */
.scenario-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start;}
.panel-box{}
.panel-tag{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:8px;padding:4px 12px;font-size:12px;font-weight:700;color:var(--muted);margin-bottom:10px;}
.panel-illus{height:230px;border-radius:18px;border:1px solid #e6dccb;background:linear-gradient(135deg,#fde7d6,#f7ddf0);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;}
.panel-illus .illus-tag{font-family:monospace;font-size:12px;letter-spacing:1px;color:#7a6a55;}
.panel-illus .illus-note{font-family:monospace;font-size:12px;color:#8a7a68;text-align:center;max-width:80%;}
.scene-text{margin-top:16px;font-size:17px;line-height:1.6;}
.choice-box{}
.choice-title{font-size:24px;font-weight:800;margin-bottom:16px;}
.choice{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;
  margin-bottom:12px;text-decoration:none;color:var(--ink);font-size:16px;box-shadow:0 4px 10px rgba(31,39,51,.05);transition:border-color .15s ease;}
.choice:hover{border-color:var(--blue-2);background:#f7fbff;}
.choice-letter{width:34px;height:34px;flex:0 0 auto;border-radius:9px;background:#eef1f7;display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--blue-2);}
.choice-note{font-size:13px;color:var(--muted);margin-top:6px;}

/* ---------- Consequence (Screen 6) ---------- */
.result-badge{display:inline-block;background:linear-gradient(135deg,var(--green-1),var(--green-2));color:#fff;font-weight:700;font-size:13px;
  padding:7px 16px;border-radius:999px;margin-bottom:14px;box-shadow:0 6px 14px rgba(46,168,100,.28);}
.result-box{background:#fff;border-radius:var(--radius);padding:26px;box-shadow:var(--shadow);}
.result-text{font-size:17px;line-height:1.7;}
.tandaan-box{background:#fdf6e3;border:1px solid #f0e2b6;border-radius:14px;padding:18px 20px;margin-top:18px;color:#7a6320;}
.tandaan-title{font-weight:700;margin-bottom:6px;}
.result-actions{display:flex;gap:14px;margin-top:22px;flex-wrap:wrap;}
@media (max-width:900px){ .scenario-grid{grid-template-columns:1fr;} }
'''

if "scenario-grid" not in style_css:
    style_css = style_css + extra_css

files = {
    "main.py": main_py,
    "templates/scenario.html": scenario_html,
    "templates/consequence.html": consequence_html,
    "static/style.css": style_css,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa/Inayos:", path)

print("\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Subukan: http://127.0.0.1:8000/mga-kuwento -> Simulan ang unang kuwento")
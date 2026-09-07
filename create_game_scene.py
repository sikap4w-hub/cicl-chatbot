import os
import json

# ============================================================
# Desk scene + dialogue engine (data-driven mula sa JSON).
# Placeholder na mukha muna; papalitan ng AI art mamaya.
# Patakbuhin: python create_game_scene.py
# ============================================================

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("game_data", exist_ok=True)

# ------------------------------------------------------------
# game_data/storyboards.json  (bagong schema; cellphone kumpleto)
# ------------------------------------------------------------
data = {
    "storyboards": [
        {
            "id": "cellphone",
            "title": "Ang Cellphone sa Palengke",
            "short": "Pagkuha ng cellphone at ang maaaring legal na consequence.",
            "color": "orange",
            "status": "ready",
            "bata": {"label": "Bata A", "art": "bata01", "mood_start": "neutral"},
            "intro": "Kumusta po. Nahiram ko lang naman po kasi yung cellphone sa palengke, balak ko naman po sanang isauli.",
            "ebidensya": [
                {"label": "Testimonya ng tindera", "text": "Nakita kong kinuha ng bata ang phone sa mesa at umalis agad, walang nagpaalam kahit kanino."}
            ],
            "tanong": [
                {"q": "Kilala mo ba ang may-ari ng phone?", "sagot": "Hindi po... pero nasa mesa lang po siya, akala ko okay lang.", "mood": "kabado"},
                {"q": "Sino ang nagbigay ng pahintulot na kunin ito?", "sagot": "Wala po... pero balak ko naman po talagang isauli.", "mood": "malungkot"}
            ],
            "sugarcoat": {"phrase": "nahiram ko lang", "totoo": "kinuha nang walang pahintulot"},
            "pagbasa": [
                {"text": "Hiniram na may pahintulot ng may-ari", "tama": False},
                {"text": "Kinuha nang walang pahintulot", "tama": True}
            ],
            "resulta": {
                "tapat": "Ang totoo, kinuha ang phone nang walang paalam, na maaaring maituring na pagnanakaw.",
                "bakit": "Ang pagkuha ng gamit ng iba nang walang pahintulot ay mali, kahit may balak na isauli.",
                "tamang_landas": "Sa ilalim ng RA 9344, kung labing-lima pababa ang bata, dadaan sa intervention program; kung labing-anim hanggang labing-pito at may discernment, sa diversion. Layunin ay maituwid, hindi parusahan.",
                "huwag_tularan": "Ang ganitong gawi ay hindi dapat tularan, ngunit laging may pagkakataong magbago at itama."
            },
            "summary": [
                "Ang magagandang salita ay hindi nagbabago sa totoong nangyari.",
                "Ang exemption ay hindi pagtakas sa responsibilidad.",
                "Mahalagang alamin ang totoo bago humusga.",
                "May tamang landas at tulong sa ilalim ng RA 9344."
            ]
        },
        {"id": "nawawalang-gamit", "title": "Ang Nawawalang Gamit", "short": "Gamit na nahanap at hindi naibalik.", "color": "purple", "status": "soon"},
        {"id": "away-eskwelahan", "title": "Ang Away sa Eskwelahan", "short": "Hindi pagkakaunawaan at kung paano naresolba.", "color": "blue", "status": "soon"},
        {"id": "saradong-lugar", "title": "Ang Pagpasok sa Saradong Lugar", "short": "Lugar na hindi pwedeng pasukan.", "color": "green", "status": "soon"},
        {"id": "bagay-hindi-iyo", "title": "Ang Bagay na Hindi Iyo", "short": "Pag-angkin ng bagay na iba ang may-ari.", "color": "pink", "status": "soon"},
        {"id": "online-problema", "title": "Ang Online na Problema", "short": "Post at mensahe sa internet.", "color": "purple", "status": "soon"},
        {"id": "gulong-nasira", "title": "Ang Gulong Nasira", "short": "Gamit ng iba na napinsala.", "color": "blue", "status": "soon"},
        {"id": "pagsama-kaibigan", "title": "Ang Pagsama sa Kaibigan", "short": "Presyur mula sa barkada.", "color": "green", "status": "soon"},
        {"id": "hindi-inaasahan", "title": "Ang Hindi Inaasahang Pangyayari", "short": "Aksidenteng may kinalaman sa iba.", "color": "pink", "status": "soon"},
        {"id": "maling-desisyon", "title": "Ang Maling Desisyon", "short": "Desisyong may kasunod na consequence.", "color": "purple", "status": "soon"}
    ]
}
with open("game_data/storyboards.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Ginawa: game_data/storyboards.json")

# ------------------------------------------------------------
# main.py  (scenario route -> game_scene.html na may embedded JSON)
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


@app.get("/kuwento/{sid}", response_class=HTMLResponse)
def scenario_page(request: Request, sid: str):
    story = get_story(sid)
    if not story or story.get("status") != "ready":
        return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Ginagawa pa ang kuwentong ito"})
    case_json = json.dumps(story, ensure_ascii=False)
    return templates.TemplateResponse(request, "game_scene.html", {"active": "game", "story": story, "case_json": case_json})


@app.get("/kuwento/{sid}/tapos", response_class=HTMLResponse)
def end_page(request: Request, sid: str):
    return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "End Summary"})


class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
def chat_api(payload: ChatMessage):
    text = payload.message.strip()
    low = text.lower()
    if not text:
        return {"reply": "Pakisulat po ang tanong ninyo."}
    if "ra 9344" in low or "9344" in low:
        return {"reply": "Ang RA 9344 po ay ang Juvenile Justice and Welfare Act."}
    if "diversion" in low:
        return {"reply": "Ang diversion po ay alternatibong proseso na hindi dumadaan agad sa korte."}
    return {"reply": "Naitala ko po ang tanong ninyo. (Placeholder muna ang sagot.)"}
'''

# ------------------------------------------------------------
# templates/game_scene.html
# ------------------------------------------------------------
game_scene_html = '''{% extends "base.html" %}
{% block content %}
<div class="chat-header">
  <a href="/mga-kuwento" class="back-btn">&larr;</a>
  <div>
    <div class="chat-title">{{ story.title }}</div>
    <div class="chat-status">Kaso &middot; Kuwentong gawa-gawa lang</div>
  </div>
</div>

<div class="scene-layout">
  <div class="scene-main" id="scene-main">
    <div class="desk">
      <div id="character" class="character"></div>
    </div>
    <div id="dialogue" class="dialogue-box"></div>
    <div id="controls" class="controls"></div>
  </div>

  <aside class="scene-side">
    <div class="side-label">MGA EBIDENSYA</div>
    <div id="evidence-list"></div>
  </aside>
</div>

<script>window.CASE = {{ case_json|safe }};</script>
<script src="/static/game.js"></script>
{% endblock %}
'''

# ------------------------------------------------------------
# static/game.js  (ang dialogue engine)
# ------------------------------------------------------------
game_js = '''(function () {
  const CASE = window.CASE;
  if (!CASE) return;

  const charEl = document.getElementById("character");
  const dialogueEl = document.getElementById("dialogue");
  const controlsEl = document.getElementById("controls");
  const evidenceEl = document.getElementById("evidence-list");
  const sceneMain = document.getElementById("scene-main");

  // ----- Placeholder na mukha (papalitan ng AI art) -----
  function face(mood) {
    const mouths = {
      neutral: '<path d="M50 74 h20" stroke="#5a4632" stroke-width="2.4" stroke-linecap="round"/>',
      kabado:  '<path d="M50 74 q5 5 10 0 q5 -5 10 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M86 50 q4 6 0 10 q-4 -4 0 -10" fill="#7ec8ff"/>',
      malungkot:'<path d="M50 78 q10 -8 20 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/>',
      ginhawa: '<path d="M50 72 q10 9 20 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    };
    const brows = {
      neutral: '<path d="M44 48 h10 M66 48 h10" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      kabado:  '<path d="M44 46 l10 -2 M76 46 l-10 -2" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      malungkot:'<path d="M44 46 l10 2 M76 46 l-10 2" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      ginhawa: '<path d="M44 47 h10 M66 47 h10" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>'
    };
    return '<svg viewBox="0 0 120 170" width="150" height="212">' +
      '<rect x="34" y="96" width="52" height="66" rx="14" fill="#7a3ff0"/>' +   // damit
      '<rect x="32" y="22" width="56" height="66" rx="26" fill="#f4c9a3"/>' +    // ulo
      '<path d="M30 40 q30 -30 60 0 q-6 -18 -30 -18 q-24 0 -30 18z" fill="#3a2a1a"/>' + // buhok
      '<circle cx="52" cy="58" r="3.4" fill="#333"/><circle cx="68" cy="58" r="3.4" fill="#333"/>' +
      (brows[mood] || brows.neutral) + (mouths[mood] || mouths.neutral) +
      '</svg>';
  }
  function setMood(m) {
    charEl.innerHTML = face(m);
    charEl.classList.toggle("shake", m === "kabado");
  }

  // ----- Typewriter -----
  let typing = null;
  function typeText(text, cb) {
    if (typing) clearInterval(typing);
    dialogueEl.textContent = "";
    let i = 0;
    typing = setInterval(function () {
      dialogueEl.textContent += text.charAt(i);
      i++;
      if (i >= text.length) { clearInterval(typing); typing = null; if (cb) cb(); }
    }, 18);
  }

  function clearControls() { controlsEl.innerHTML = ""; }
  function addBtn(label, cls, onclick) {
    const b = document.createElement("button");
    b.className = cls;
    b.textContent = label;
    b.addEventListener("click", onclick);
    controlsEl.appendChild(b);
    return b;
  }

  // ----- Ebidensya -----
  function renderEvidence() {
    evidenceEl.innerHTML = "";
    (CASE.ebidensya || []).forEach(function (e) {
      const card = document.createElement("div");
      card.className = "evi-card";
      card.innerHTML = '<div class="evi-label">' + e.label + '</div><div class="evi-text">' + e.text + '</div>';
      evidenceEl.appendChild(card);
    });
  }

  // ----- States -----
  function startIntro() {
    setMood(CASE.bata && CASE.bata.mood_start ? CASE.bata.mood_start : "neutral");
    typeText(CASE.intro, function () {
      clearControls();
      addBtn("Magtanong \\u203a", "btn btn--blue", startQuestioning);
    });
  }

  const asked = {};
  function startQuestioning() {
    renderEvidence();
    clearControls();
    (CASE.tanong || []).forEach(function (t, i) {
      const b = addBtn(t.q, "q-btn", function () { askQuestion(i, b); });
    });
    addBtn("Handa na akong magpasya \\u203a", "btn btn--blue", startVerdict);
  }
  function askQuestion(i, btn) {
    const t = CASE.tanong[i];
    setMood(t.mood || "neutral");
    typeText("\\u201c" + t.sagot + "\\u201d");
    asked[i] = true;
    if (btn) btn.classList.add("asked");
  }

  function startVerdict() {
    setMood("neutral");
    clearControls();
    typeText("Batay sa kuwento at ebidensya, ano ang masasabi mo?", function () {
      addBtn("Nauunawaan", "btn btn--green", function () { chooseVerdict("clear"); });
      addBtn("Suriin pa", "btn btn--orange", function () { chooseVerdict("inspect"); });
    });
  }
  function chooseVerdict(v) {
    const hasSugar = !!CASE.sugarcoat;
    if (v === "clear" && hasSugar) {
      clearControls();
      typeText("Mukhang may hindi pa tugma sa ebidensya. Suriin pa natin.", function () {
        addBtn("Suriin pa", "btn btn--orange", function () { chooseVerdict("inspect"); });
      });
      return;
    }
    if (v === "inspect") { startReading(); return; }
    showResulta();
  }

  function startReading() {
    clearControls();
    typeText("Ano ang totoong nangyari, batay sa ebidensya?", function () {
      (CASE.pagbasa || []).forEach(function (opt) {
        addBtn(opt.text, "q-btn", function () { chooseReading(opt); });
      });
    });
  }
  function chooseReading(opt) {
    if (!opt.tama) {
      clearControls();
      typeText("Tignan pa natin ang ebidensya. Subukan muli.", function () { startReading(); });
      return;
    }
    showResulta();
  }

  function showResulta() {
    setMood("ginhawa");
    const r = CASE.resulta || {};
    let html = '<div class="result-badge">\\u24d8 Pang-edukasyon na resulta</div>';
    html += '<div class="result-box"><p class="result-text"><b>Ang totoo:</b> ' + (r.tapat || "") + '</p>';
    if (r.bakit) html += '<p class="result-text">' + r.bakit + '</p>';
    if (r.tamang_landas) html += '<p class="result-text"><b>Tamang landas:</b> ' + r.tamang_landas + '</p>';
    html += '</div>';
    if (r.huwag_tularan) html += '<div class="tandaan-box"><div class="tandaan-title">\\ud83d\\udee1 Mahalagang Tandaan</div><p>' + r.huwag_tularan + '</p></div>';
    html += '<div class="result-actions"><a href="/kuwento/' + CASE.id + '/tapos" class="btn btn--blue">Magpatuloy \\u203a</a>' +
            '<a href="/kuwento/' + CASE.id + '" class="btn btn--ghost">Ulitin</a></div>';
    sceneMain.innerHTML = html;
  }

  startIntro();
})();
'''

# ------------------------------------------------------------
# static/style.css  (idagdag ang desk scene CSS)
# ------------------------------------------------------------
style_css = open("static/style.css", encoding="utf-8").read()

scene_css = '''

/* ---------- Desk scene ---------- */
.scene-layout{display:flex;gap:20px;align-items:flex-start;}
.scene-main{flex:1;min-width:0;}
.desk{height:280px;border-radius:20px;position:relative;overflow:hidden;
  background:linear-gradient(180deg,#eaf0fb 0%,#dfe6f6 70%,#c9b79a 70%,#b8a486 100%);
  display:flex;align-items:flex-end;justify-content:center;}
.character{margin-bottom:34px;animation:bob 3.2s ease-in-out infinite;transform-origin:center bottom;}
@keyframes bob{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
.character.shake{animation:shake .5s ease-in-out infinite;}
@keyframes shake{0%,100%{transform:translateX(0);}25%{transform:translateX(-2px);}75%{transform:translateX(2px);}}
.dialogue-box{background:#fff;border-radius:16px;padding:20px 22px;margin-top:16px;min-height:76px;
  font-size:17px;line-height:1.6;box-shadow:var(--shadow);}
.controls{margin-top:16px;display:flex;flex-wrap:wrap;gap:10px;}
.q-btn{text-align:left;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 16px;
  font-size:15px;color:var(--ink);cursor:pointer;box-shadow:0 4px 10px rgba(31,39,51,.05);}
.q-btn:hover{background:#f7fbff;border-color:var(--blue-2);}
.q-btn.asked{opacity:.55;}
.scene-side{width:280px;flex:0 0 auto;}
.evi-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px;box-shadow:0 4px 10px rgba(31,39,51,.05);}
.evi-label{font-weight:700;font-size:14px;margin-bottom:4px;}
.evi-text{font-size:14px;color:var(--muted);}
@media (max-width:900px){ .scene-layout{flex-direction:column;} .scene-side{width:100%;} }
'''

if "scene-layout" not in style_css:
    style_css = style_css + scene_css

files = {
    "main.py": main_py,
    "templates/game_scene.html": game_scene_html,
    "static/game.js": game_js,
    "static/style.css": style_css,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa/Inayos:", path)

print("\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Subukan: http://127.0.0.1:8000/mga-kuwento -> Simulan ang unang kaso")
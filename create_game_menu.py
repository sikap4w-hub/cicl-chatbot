import os
import json

# ============================================================
# Screen 4: Game Menu / Story List + storyboards.json data file.
# Ang unang kuwento ay kumpleto; ang siyam ay stub muna.
# Patakbuhin: python create_game_menu.py
# ============================================================

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("game_data", exist_ok=True)

# ------------------------------------------------------------
# game_data/storyboards.json  (laman ng laro)
# ------------------------------------------------------------
storyboards = {
    "storyboards": [
        {
            "id": "cellphone",
            "title": "Ang Cellphone sa Palengke",
            "short": "Pagkuha ng cellphone at ang maaaring legal na consequence.",
            "color": "orange",
            "status": "ready",
            "scenes": [
                {
                    "panel": 1,
                    "total": 6,
                    "illustration": "dalawang kabataan sa palengke, cellphone na naiwan sa mesa",
                    "text": "Habang nasa palengke ka kasama ang iyong kaibigan, may napansin kang cellphone na naiwan sa isang mesa.",
                    "question": "Ano ang gagawin mo?",
                    "choices": [
                        {"id": "A", "text": "Kunin ito at itago.", "consequence": "c_take"},
                        {"id": "B", "text": "Ibigay ito sa may-ari o sa isang adult na maaaring tumulong.", "consequence": "c_return"},
                        {"id": "C", "text": "Huwag itong galawin at umalis.", "consequence": "c_leave"}
                    ]
                }
            ],
            "consequences": {
                "c_take": {
                    "result": "Dahil labing-lima ka pa lang, maaaring iba ang proseso na susundin kumpara sa isang adult. Sa ilalim ng RA 9344, may mga espesyal na proseso at intervention para sa mga batang nasasangkot sa offense, depende sa kanilang edad at sa sitwasyon.",
                    "tandaan": "Ang intervention ay bahagi ng proseso upang matulungan ang bata na maunawaan ang nangyari at makabalik nang maayos sa komunidad. Ang exemption ay hindi pagtakas sa responsibilidad."
                },
                "c_return": {
                    "result": "Magandang desisyon. Ang pagbabalik ng nawawalang gamit sa may-ari o sa isang trusted adult ay tama at responsableng gawain. Walang offense na nangyari.",
                    "tandaan": "Ang paggawa ng tama kahit walang nakakakita ay tanda ng integridad."
                },
                "c_leave": {
                    "result": "Hindi ka nasangkot sa anumang offense dahil hindi mo ginalaw ang gamit. Gayunpaman, mas makakatulong kung ipagbibigay-alam ito sa isang adult.",
                    "tandaan": "Ang pag-iwas sa maling gawa ay mabuti; ang pagtulong na maibalik ito sa may-ari ay mas mabuti pa."
                }
            },
            "summary": [
                "Ang exemption ay hindi pagtakas sa responsibilidad.",
                "Mahalagang malaman ang iyong mga karapatan.",
                "May mga espesyal na proseso para sa mga batang nasasangkot sa offense.",
                "Mahalagang humingi ng tulong sa isang trusted adult o tamang support system kapag kinakailangan."
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
    json.dump(storyboards, f, indent=2, ensure_ascii=False)
print("Ginawa: game_data/storyboards.json")

# ------------------------------------------------------------
# main.py  (idinagdag: pagbasa ng JSON + game menu route)
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
    # Stub muna; gagawin ang totoong scenario screen sa susunod na hakbang.
    return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Game Scenario"})


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
    return {"reply": "Naitala ko po ang tanong ninyo. (Placeholder muna ang sagot; ikakabit ang totoong chatbot mamaya.)"}
'''

# ------------------------------------------------------------
# templates/game_menu.html
# ------------------------------------------------------------
game_menu_html = '''{% extends "base.html" %}
{% block content %}
<div class="menu-top">
  <div class="ribbon ribbon-orange">MAGLARO</div>
  <span class="note-badge">&#9432; Kuwentong gawa-gawa lang ang mga ito.</span>
</div>
<h1 class="page-title">Pumili ng Kuwento</h1>
<p class="page-sub">Pumili ng sitwasyon at alamin kung ano ang maaaring mangyari.</p>

<div class="story-grid">
  {% for s in storyboards %}
  <div class="story-card">
    <div class="story-icon icon-{{ s.color }}">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="1.9"><rect x="3" y="8" width="18" height="9" rx="4.5"/><path d="M8 12v3M6.5 13.5h3" stroke-linecap="round"/></svg>
    </div>
    <div class="story-info">
      <div class="story-title">{{ s.title }}</div>
      <div class="story-desc">{{ s.short }}</div>
    </div>
    {% if s.status == 'ready' %}
      <a href="/kuwento/{{ s.id }}" class="btn btn--orange story-btn">Simulan &rsaquo;</a>
    {% else %}
      <span class="story-arrow">&rsaquo;</span>
    {% endif %}
  </div>
  {% endfor %}
</div>
{% endblock %}
'''

# ------------------------------------------------------------
# static/style.css  (base + chat + game menu, buong file)
# ------------------------------------------------------------
style_css = open("static/style.css", encoding="utf-8").read() if os.path.exists("static/style.css") else ""

game_css = '''

/* ---------- Game menu / story list ---------- */
.menu-top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;}
.note-badge{background:#fdf6e3;border:1px solid #f0e2b6;color:#7a6320;padding:8px 16px;border-radius:999px;font-size:14px;}
.ribbon-orange{background:linear-gradient(135deg,var(--orange-1),var(--orange-2));}
.story-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.story-card{display:flex;align-items:center;gap:14px;background:#fff;border-radius:16px;padding:16px 18px;box-shadow:var(--shadow);}
.story-icon{width:48px;height:48px;border-radius:12px;flex:0 0 auto;display:flex;align-items:center;justify-content:center;}
.icon-blue{background:linear-gradient(135deg,var(--blue-1),var(--blue-2));}
.icon-green{background:linear-gradient(135deg,var(--green-1),var(--green-2));}
.icon-pink{background:linear-gradient(135deg,#f78fb3,#e0537d);}
.story-info{flex:1;min-width:0;}
.story-title{font-weight:700;font-size:17px;}
.story-desc{color:var(--muted);font-size:14px;}
.story-btn{min-height:42px;padding:0 20px;font-size:15px;}
.story-arrow{color:#c2c6d0;font-size:24px;padding:0 10px;}
@media (max-width:900px){ .story-grid{grid-template-columns:1fr;} }
'''

# Siguraduhing may base+chat CSS; kung wala, huwag lang mag-crash.
if "--blue-1" not in style_css:
    # fallback: minimal variables lang (dapat hindi mangyari kung na-run na ang create_chat.py)
    style_css = ":root{--blue-1:#38b6ff;--blue-2:#1f7fe0;--orange-1:#ffa64d;--orange-2:#f2651a;--green-1:#57cc86;--green-2:#2ea864;--muted:#6b7280;--shadow:0 12px 30px rgba(31,39,51,.10);}\n" + style_css

# Idempotent: idagdag lang ang game CSS kung wala pa
if "story-grid" not in style_css:
    style_css = style_css + game_css

files = {
    "main.py": main_py,
    "templates/game_menu.html": game_menu_html,
    "static/style.css": style_css,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa/Inayos:", path)

print("\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Tapos: http://127.0.0.1:8000/mga-kuwento")
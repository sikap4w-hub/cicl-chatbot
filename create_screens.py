import os

# ============================================================
# Ginagawa nito ang Screen 1 (Welcome) at Screen 2 (Dashboard)
# base sa mock-up. Patakbuhin: python create_screens.py
# ============================================================

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# ------------------------------------------------------------
# main.py  -> routes para sa bawat screen (bawat isa, tunay na URL)
# ------------------------------------------------------------
main_py = '''from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE = Path(__file__).parent
app = FastAPI(title="Kaalaman at Karapatan")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


# ---------- Screen 1: Welcome / Landing ----------
@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


# ---------- Screen 2: Main Menu / Dashboard ----------
@app.get("/menu", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "active": "home"})


# ---------- Placeholder muna para sa mga susunod na screen ----------
@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse("soon.html", {"request": request, "active": "chat", "title": "Makipag-usap"})


@app.get("/mga-kuwento", response_class=HTMLResponse)
def stories_page(request: Request):
    return templates.TemplateResponse("soon.html", {"request": request, "active": "game", "title": "Maglaro"})


# ---------- Chat API (placeholder logic muna) ----------
class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
def chat_api(payload: ChatMessage):
    text = payload.message.strip().lower()
    if not text:
        return {"reply": "Pakisulat po ang tanong ninyo."}
    if "diversion" in text:
        return {"reply": "Ang diversion po ay alternatibong proseso na hindi dumadaan agad sa korte."}
    return {"reply": "Naitala ko po ang mensahe ninyo. (Placeholder muna ang sagot.)"}
'''

# ------------------------------------------------------------
# templates/base.html  -> ang shell na may sidebar rail (Screen 2+)
# ------------------------------------------------------------
base_html = '''<!DOCTYPE html>
<html lang="tl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kaalaman at Karapatan</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div class="app-shell">
    <aside class="rail">
      <div class="brand">
        <span class="logo">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
            <path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/>
            <path d="M9.3 12l1.9 1.9L15 10.2" stroke="#1f7fe0" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="brand-name">Kaalaman at<br>Karapatan</span>
      </div>

      <nav class="nav">
        <a href="/menu" class="nav-item home {% if active == 'home' %}active{% endif %}">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 11l8-6 8 6M6 10v9h12v-9" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>Home</span>
        </a>
        <a href="/chat" class="nav-item chat {% if active == 'chat' %}active{% endif %}">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 5h14v10H9l-4 4V5z" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>Makipag-usap</span>
        </a>
        <a href="/mga-kuwento" class="nav-item game {% if active == 'game' %}active{% endif %}">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="8" width="18" height="9" rx="4.5"/><path d="M8 12v3M6.5 13.5h3" stroke-linecap="round"/></svg>
          <span>Maglaro</span>
        </a>
      </nav>

      <div class="rail-footer">
        <div class="badge badge-green">✓ Anonymous session</div>
        <a href="#" class="nav-item muted-item"><span>Tulong</span></a>
      </div>
    </aside>

    <main class="content">
      {% block content %}{% endblock %}
    </main>
  </div>
  <script src="/static/script.js"></script>
</body>
</html>
'''

# ------------------------------------------------------------
# templates/welcome.html  -> Screen 1 (walang rail)
# ------------------------------------------------------------
welcome_html = '''<!DOCTYPE html>
<html lang="tl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kaalaman at Karapatan</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body class="welcome-bg">
  <header class="topbar">
    <div class="brand">
      <span class="logo">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
          <path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/>
          <path d="M9.3 12l1.9 1.9L15 10.2" stroke="#1f7fe0" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
      <span class="brand-name-inline">Kaalaman at Karapatan</span>
    </div>
    <div class="lang-toggle">
      <button class="lang on">Filipino</button>
      <button class="lang">English</button>
    </div>
  </header>

  <main class="hero">
    <div class="hero-left">
      <div class="badge badge-green">✓ Walang account. Anonymous.</div>
      <h1 class="hero-title">Kaalaman at<br>Karapatan</h1>
      <p class="hero-sub">Ligtas na lugar para magtanong tungkol sa iyong mga karapatan.</p>
      <div class="hero-actions">
        <a href="/menu" class="btn btn--blue">Magsimula <span class="arrow">&rsaquo;</span></a>
        <a href="#" class="btn btn--ghost">&#9432; Paano ito gumagana</a>
      </div>
      <p class="fineprint">Hindi kami nangongolekta ng pangalan o personal na impormasyon.</p>
    </div>
    <div class="hero-right">
      <div class="illus-box">
        <div class="illus-tag">HERO ILLUSTRATION</div>
        <p class="illus-note">kabataan na nag-aaral tungkol sa kanyang mga karapatan</p>
      </div>
    </div>
  </main>
</body>
</html>
'''

# ------------------------------------------------------------
# templates/dashboard.html  -> Screen 2 (extends base)
# ------------------------------------------------------------
dashboard_html = '''{% extends "base.html" %}
{% block content %}
<div class="ribbon ribbon-blue">HOME</div>
<h1 class="page-title">Ano ang gusto mong gawin?</h1>
<p class="page-sub">Pumili ng paraan para matuto tungkol sa iyong mga karapatan.</p>

<div class="card-grid">
  <div class="card">
    <div class="card-icon icon-purple">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#fff" stroke-width="1.9"><path d="M5 5h14v10H9l-4 4V5z" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <h2 class="card-title">Makipag-usap</h2>
    <p class="card-text">Magtanong tungkol sa iyong mga karapatan.</p>
    <a href="/chat" class="btn btn--purple card-btn">&#128172; Buksan ang Chat</a>
  </div>

  <div class="card">
    <div class="card-icon icon-orange">
      <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#fff" stroke-width="1.9"><rect x="3" y="8" width="18" height="9" rx="4.5"/><path d="M8 12v3M6.5 13.5h3" stroke-linecap="round"/></svg>
    </div>
    <h2 class="card-title">Maglaro</h2>
    <p class="card-text">Matuto tungkol sa legal na consequences sa pamamagitan ng kuwento.</p>
    <a href="/mga-kuwento" class="btn btn--orange card-btn">&#9638; Pumili ng Laro</a>
  </div>
</div>

<div class="infobar">&#9432; Nandito ka: Home. Ang rail sa kaliwa ay laging nakikita.</div>
{% endblock %}
'''

# ------------------------------------------------------------
# templates/soon.html  -> placeholder para sa mga di pa tapos
# ------------------------------------------------------------
soon_html = '''{% extends "base.html" %}
{% block content %}
<div class="ribbon ribbon-blue">{{ title }}</div>
<h1 class="page-title">{{ title }}</h1>
<div class="soon-box">
  <p>Ginagawa pa ang bahaging ito.</p>
  <p class="page-sub">Dito ilalagay ang {{ title }} screen mula sa mock-up.</p>
  <a href="/menu" class="btn btn--blue">Bumalik sa Home</a>
</div>
{% endblock %}
'''

# ------------------------------------------------------------
# static/style.css  -> ang buong design system
# ------------------------------------------------------------
style_css = '''* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --blue-1:#38b6ff; --blue-2:#1f7fe0;
  --purple-1:#b06ef7; --purple-2:#7a3ff0;
  --orange-1:#ffa64d; --orange-2:#f2651a;
  --green-1:#57cc86; --green-2:#2ea864;
  --ink:#1f2733; --muted:#6b7280;
  --card:#ffffff; --line:#e7e9f0;
  --cream: rgba(255,250,240,.95);
  --radius:20px; --shadow:0 12px 30px rgba(31,39,51,.10);
}
body {
  font-family: "Segoe UI", Arial, Helvetica, sans-serif;
  font-size:17px; color:var(--ink); line-height:1.5;
  background: linear-gradient(135deg,#eef2fb 0%,#f4f0fb 100%);
  min-height:100vh;
}

/* ---------- Buttons (capsule, cream-edged) ---------- */
.btn {
  display:inline-flex; align-items:center; justify-content:center; gap:8px;
  min-height:52px; padding:0 26px; border-radius:999px;
  font-size:17px; font-weight:600; text-decoration:none; cursor:pointer;
  border:none; color:#fff; transition:transform .05s ease, filter .15s ease;
  box-shadow:0 0 0 3px var(--cream), 0 8px 18px rgba(31,39,51,.18);
}
.btn:hover { filter:brightness(1.05); }
.btn:active { transform:translateY(1px); }
.btn--blue   { background:linear-gradient(135deg,var(--blue-1),var(--blue-2)); }
.btn--purple { background:linear-gradient(135deg,var(--purple-1),var(--purple-2)); }
.btn--orange { background:linear-gradient(135deg,var(--orange-1),var(--orange-2)); }
.btn--green  { background:linear-gradient(135deg,var(--green-1),var(--green-2)); }
.btn--ghost  { background:#fff; color:var(--ink); box-shadow:0 0 0 3px var(--cream),0 6px 14px rgba(31,39,51,.10); }
.arrow { font-size:22px; line-height:1; }

/* ---------- Badges ---------- */
.badge { display:inline-flex; align-items:center; gap:6px; padding:8px 16px; border-radius:999px; font-size:14px; font-weight:600; }
.badge-green { background:linear-gradient(135deg,var(--green-1),var(--green-2)); color:#fff; box-shadow:0 6px 14px rgba(46,168,100,.3); }

/* ---------- Ribbon tag ---------- */
.ribbon { display:inline-block; padding:6px 22px 6px 14px; color:#fff; font-size:13px; font-weight:700; letter-spacing:.5px;
  clip-path: polygon(0 0,100% 0,88% 50%,100% 100%,0 100%); border-radius:6px 0 0 6px; margin-bottom:14px; }
.ribbon-blue { background:linear-gradient(135deg,var(--blue-1),var(--blue-2)); }

/* ---------- Welcome screen ---------- */
.welcome-bg { background: linear-gradient(135deg,#e9f0fd 0%,#efe9fb 100%); }
.topbar { display:flex; align-items:center; justify-content:space-between; background:#fff; padding:16px 28px; box-shadow:0 2px 10px rgba(31,39,51,.05); }
.brand { display:flex; align-items:center; gap:12px; }
.logo { width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,var(--blue-1),var(--blue-2)); box-shadow:0 4px 10px rgba(31,127,224,.35); }
.brand-name { font-weight:700; font-size:15px; line-height:1.2; }
.brand-name-inline { font-weight:700; font-size:18px; }
.lang-toggle { display:flex; background:#eef1f7; border-radius:999px; padding:4px; gap:2px; }
.lang { border:none; background:transparent; padding:8px 18px; border-radius:999px; font-size:14px; cursor:pointer; color:var(--muted); }
.lang.on { background:linear-gradient(135deg,var(--blue-1),var(--blue-2)); color:#fff; font-weight:600; }

.hero { display:grid; grid-template-columns:1fr 1fr; gap:40px; max-width:1100px; margin:0 auto; padding:70px 28px; align-items:center; }
.hero-title { font-size:52px; font-weight:800; line-height:1.05; margin:18px 0 14px; }
.hero-sub { font-size:19px; color:#4b5563; margin-bottom:28px; }
.hero-actions { display:flex; gap:14px; flex-wrap:wrap; }
.fineprint { font-size:13px; color:var(--muted); margin-top:16px; }
.illus-box { position:relative; height:360px; border-radius:24px; border:1px solid #dfe4f5;
  background:linear-gradient(135deg,#dbe6fb,#e7ddfb); display:flex; flex-direction:column; align-items:center; justify-content:center; }
.illus-tag { font-family:monospace; font-size:12px; letter-spacing:1px; color:#5b6474; margin-top:8px; }
.illus-note { font-family:monospace; font-size:12px; color:#7a8090; text-align:center; max-width:70%; margin-top:6px; }

/* ---------- App shell (rail + content) ---------- */
.app-shell { display:flex; min-height:100vh; }
.rail { width:250px; background:#fff; border-right:1px solid var(--line); padding:22px 16px; display:flex; flex-direction:column; }
.rail .brand { margin-bottom:26px; }
.nav { display:flex; flex-direction:column; gap:6px; flex:1; }
.nav-item { display:flex; align-items:center; gap:12px; padding:13px 16px; border-radius:12px; text-decoration:none;
  color:var(--ink); font-weight:600; font-size:16px; }
.nav-item:hover { background:#f3f5fa; }
.nav-item.active.home  { background:linear-gradient(135deg,var(--blue-1),var(--blue-2));   color:#fff; box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(31,127,224,.28); }
.nav-item.active.chat  { background:linear-gradient(135deg,var(--purple-1),var(--purple-2)); color:#fff; box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(122,63,240,.28); }
.nav-item.active.game  { background:linear-gradient(135deg,var(--orange-1),var(--orange-2)); color:#fff; box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(242,101,26,.28); }
.rail-footer { margin-top:auto; display:flex; flex-direction:column; gap:8px; }
.muted-item { color:var(--muted); font-weight:500; font-size:15px; }

.content { flex:1; padding:36px 44px; max-width:1000px; }
.page-title { font-size:34px; font-weight:800; margin-bottom:6px; }
.page-sub { font-size:17px; color:var(--muted); margin-bottom:26px; }

/* ---------- Cards ---------- */
.card-grid { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
.card { background:var(--card); border-radius:var(--radius); padding:26px; box-shadow:var(--shadow); }
.card-icon { width:56px; height:56px; border-radius:16px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.icon-purple { background:linear-gradient(135deg,var(--purple-1),var(--purple-2)); box-shadow:0 6px 14px rgba(122,63,240,.3); }
.icon-orange { background:linear-gradient(135deg,var(--orange-1),var(--orange-2)); box-shadow:0 6px 14px rgba(242,101,26,.3); }
.card-title { font-size:22px; font-weight:700; margin-bottom:6px; }
.card-text { color:var(--muted); margin-bottom:20px; }
.card-btn { width:100%; }
.infobar { margin-top:24px; background:#fff; border-radius:14px; padding:16px 20px; color:#4b5563; font-size:15px; box-shadow:0 6px 16px rgba(31,39,51,.06); }

.soon-box { background:#fff; border-radius:var(--radius); padding:40px; box-shadow:var(--shadow); text-align:center; }
.soon-box p { margin-bottom:12px; }
.soon-box .btn { margin-top:14px; }

/* ---------- Responsive (rail -> top under 900px) ---------- */
@media (max-width:900px) {
  .app-shell { flex-direction:column; }
  .rail { width:100%; flex-direction:row; align-items:center; overflow-x:auto; }
  .rail .brand { margin:0 16px 0 0; }
  .nav { flex-direction:row; }
  .rail-footer { flex-direction:row; margin:0 0 0 auto; }
  .hero { grid-template-columns:1fr; }
  .card-grid { grid-template-columns:1fr; }
  .hero-title { font-size:40px; }
}
'''

# ------------------------------------------------------------
# static/script.js  -> maliit lang muna (language toggle)
# ------------------------------------------------------------
script_js = '''// Language toggle (visual muna)
document.querySelectorAll(".lang").forEach(function (btn) {
  btn.addEventListener("click", function () {
    document.querySelectorAll(".lang").forEach(function (b) { b.classList.remove("on"); });
    btn.classList.add("on");
  });
});
'''

files = {
    "main.py": main_py,
    "templates/base.html": base_html,
    "templates/welcome.html": welcome_html,
    "templates/dashboard.html": dashboard_html,
    "templates/soon.html": soon_html,
    "static/style.css": style_css,
    "static/script.js": script_js,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa:", path)

print("\nTapos na! Patakbuhin: uvicorn main:app --reload")
print("Tapos buksan sa browser: http://127.0.0.1:8000")

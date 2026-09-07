import os

# ============================================================
# Screen 3: Chatbot. Inaayos din ang main.py (TemplateResponse
# new signature) at ikinakabit ang gumaganang chat.
# Patakbuhin: python create_chat.py
# ============================================================

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# ------------------------------------------------------------
# main.py  (bagong signature na: request muna)
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
    return templates.TemplateResponse(request, "soon.html", {"active": "game", "title": "Maglaro"})


# ---------- Chat API (placeholder logic muna; papalitan ng SOP 2) ----------
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
# templates/chat.html
# ------------------------------------------------------------
chat_html = '''{% extends "base.html" %}
{% block content %}
<div class="chat-header">
  <a href="/menu" class="back-btn">&larr;</a>
  <div>
    <div class="chat-title">Makipag-usap</div>
    <div class="chat-status"><span class="dot"></span> KARAPATAN Assistant</div>
  </div>
</div>

<div class="chat-body">
  <div class="chat-main">
    <div class="messages" id="messages">
      <div class="msg system">Ang impormasyon dito ay para makatulong sa pag-unawa sa iyong mga karapatan.</div>
      <div class="msg bot">
        <span class="avatar">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none"><path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/></svg>
        </span>
        <div class="bubble">Kumusta! Maaari mo akong tanungin tungkol sa iyong mga karapatan.</div>
      </div>
    </div>

    <div class="chat-input">
      <input id="user-input" type="text" placeholder="I-type ang iyong tanong..." autocomplete="off">
      <button id="mic-btn" class="mic-btn" title="Speech input (ginagawa pa)">&#127908;</button>
      <button id="send-btn" class="btn btn--purple send-btn">&#10148; Ipadala</button>
    </div>
  </div>

  <aside class="chat-side">
    <div class="side-label">MGA PUWEDENG ITANONG</div>
    <button class="quick-q">Ano ang RA 9344?</button>
    <button class="quick-q">Sino ang makakatulong sa akin?</button>
    <button class="quick-q">Ano ang intervention program?</button>
    <button class="quick-q">May karapatan ba akong tumahimik?</button>

    <div class="paalala">
      <div class="paalala-title">&#9432; Paalala</div>
      <div>Hindi ito legal advice. Para sa tunay na kaso, kumausap ng abogado o trusted adult.</div>
    </div>
  </aside>
</div>
{% endblock %}
'''

# ------------------------------------------------------------
# static/style.css  (base + chat, buong file para idempotent)
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
body { font-family:"Segoe UI",Arial,Helvetica,sans-serif; font-size:17px; color:var(--ink); line-height:1.5;
  background:linear-gradient(135deg,#eef2fb 0%,#f4f0fb 100%); min-height:100vh; }

.btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:52px; padding:0 26px;
  border-radius:999px; font-size:17px; font-weight:600; text-decoration:none; cursor:pointer; border:none; color:#fff;
  transition:transform .05s ease,filter .15s ease; box-shadow:0 0 0 3px var(--cream),0 8px 18px rgba(31,39,51,.18); }
.btn:hover { filter:brightness(1.05); } .btn:active { transform:translateY(1px); }
.btn--blue{background:linear-gradient(135deg,var(--blue-1),var(--blue-2));}
.btn--purple{background:linear-gradient(135deg,var(--purple-1),var(--purple-2));}
.btn--orange{background:linear-gradient(135deg,var(--orange-1),var(--orange-2));}
.btn--green{background:linear-gradient(135deg,var(--green-1),var(--green-2));}
.btn--ghost{background:#fff;color:var(--ink);box-shadow:0 0 0 3px var(--cream),0 6px 14px rgba(31,39,51,.10);}
.arrow{font-size:22px;line-height:1;}

.badge{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:999px;font-size:14px;font-weight:600;}
.badge-green{background:linear-gradient(135deg,var(--green-1),var(--green-2));color:#fff;box-shadow:0 6px 14px rgba(46,168,100,.3);}

.ribbon{display:inline-block;padding:6px 22px 6px 14px;color:#fff;font-size:13px;font-weight:700;letter-spacing:.5px;
  clip-path:polygon(0 0,100% 0,88% 50%,100% 100%,0 100%);border-radius:6px 0 0 6px;margin-bottom:14px;}
.ribbon-blue{background:linear-gradient(135deg,var(--blue-1),var(--blue-2));}

.welcome-bg{background:linear-gradient(135deg,#e9f0fd 0%,#efe9fb 100%);}
.topbar{display:flex;align-items:center;justify-content:space-between;background:#fff;padding:16px 28px;box-shadow:0 2px 10px rgba(31,39,51,.05);}
.brand{display:flex;align-items:center;gap:12px;}
.logo{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--blue-1),var(--blue-2));box-shadow:0 4px 10px rgba(31,127,224,.35);}
.brand-name{font-weight:700;font-size:15px;line-height:1.2;}
.brand-name-inline{font-weight:700;font-size:18px;}
.lang-toggle{display:flex;background:#eef1f7;border-radius:999px;padding:4px;gap:2px;}
.lang{border:none;background:transparent;padding:8px 18px;border-radius:999px;font-size:14px;cursor:pointer;color:var(--muted);}
.lang.on{background:linear-gradient(135deg,var(--blue-1),var(--blue-2));color:#fff;font-weight:600;}

.hero{display:grid;grid-template-columns:1fr 1fr;gap:40px;max-width:1100px;margin:0 auto;padding:70px 28px;align-items:center;}
.hero-title{font-size:52px;font-weight:800;line-height:1.05;margin:18px 0 14px;}
.hero-sub{font-size:19px;color:#4b5563;margin-bottom:28px;}
.hero-actions{display:flex;gap:14px;flex-wrap:wrap;}
.fineprint{font-size:13px;color:var(--muted);margin-top:16px;}
.illus-box{position:relative;height:360px;border-radius:24px;border:1px solid #dfe4f5;
  background:linear-gradient(135deg,#dbe6fb,#e7ddfb);display:flex;flex-direction:column;align-items:center;justify-content:center;}
.illus-tag{font-family:monospace;font-size:12px;letter-spacing:1px;color:#5b6474;margin-top:8px;}
.illus-note{font-family:monospace;font-size:12px;color:#7a8090;text-align:center;max-width:70%;margin-top:6px;}

.app-shell{display:flex;min-height:100vh;}
.rail{width:250px;background:#fff;border-right:1px solid var(--line);padding:22px 16px;display:flex;flex-direction:column;}
.rail .brand{margin-bottom:26px;}
.nav{display:flex;flex-direction:column;gap:6px;flex:1;}
.nav-item{display:flex;align-items:center;gap:12px;padding:13px 16px;border-radius:12px;text-decoration:none;color:var(--ink);font-weight:600;font-size:16px;}
.nav-item:hover{background:#f3f5fa;}
.nav-item.active.home{background:linear-gradient(135deg,var(--blue-1),var(--blue-2));color:#fff;box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(31,127,224,.28);}
.nav-item.active.chat{background:linear-gradient(135deg,var(--purple-1),var(--purple-2));color:#fff;box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(122,63,240,.28);}
.nav-item.active.game{background:linear-gradient(135deg,var(--orange-1),var(--orange-2));color:#fff;box-shadow:0 0 0 3px var(--cream),0 8px 16px rgba(242,101,26,.28);}
.rail-footer{margin-top:auto;display:flex;flex-direction:column;gap:8px;}
.muted-item{color:var(--muted);font-weight:500;font-size:15px;}

.content{flex:1;padding:36px 44px;max-width:1040px;}
.page-title{font-size:34px;font-weight:800;margin-bottom:6px;}
.page-sub{font-size:17px;color:var(--muted);margin-bottom:26px;}

.card-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;}
.card{background:var(--card);border-radius:var(--radius);padding:26px;box-shadow:var(--shadow);}
.card-icon{width:56px;height:56px;border-radius:16px;display:flex;align-items:center;justify-content:center;margin-bottom:16px;}
.icon-purple{background:linear-gradient(135deg,var(--purple-1),var(--purple-2));box-shadow:0 6px 14px rgba(122,63,240,.3);}
.icon-orange{background:linear-gradient(135deg,var(--orange-1),var(--orange-2));box-shadow:0 6px 14px rgba(242,101,26,.3);}
.card-title{font-size:22px;font-weight:700;margin-bottom:6px;}
.card-text{color:var(--muted);margin-bottom:20px;}
.card-btn{width:100%;}
.infobar{margin-top:24px;background:#fff;border-radius:14px;padding:16px 20px;color:#4b5563;font-size:15px;box-shadow:0 6px 16px rgba(31,39,51,.06);}
.soon-box{background:#fff;border-radius:var(--radius);padding:40px;box-shadow:var(--shadow);text-align:center;}
.soon-box p{margin-bottom:12px;} .soon-box .btn{margin-top:14px;}

/* ---------- Chat screen ---------- */
.chat-header{display:flex;align-items:center;gap:14px;margin-bottom:18px;}
.back-btn{width:44px;height:44px;border-radius:12px;background:#eef1f7;display:flex;align-items:center;justify-content:center;
  text-decoration:none;color:var(--ink);font-size:20px;}
.chat-title{font-size:22px;font-weight:800;}
.chat-status{font-size:13px;color:var(--muted);display:flex;align-items:center;gap:6px;}
.dot{width:9px;height:9px;border-radius:50%;background:var(--green-2);display:inline-block;}

.chat-body{display:flex;gap:20px;height:calc(100vh - 190px);}
.chat-main{flex:1;display:flex;flex-direction:column;background:#fff;border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden;}
.messages{flex:1;overflow-y:auto;padding:22px;display:flex;flex-direction:column;gap:14px;}
.msg{max-width:78%;}
.msg.system{align-self:center;background:#f0ebfb;color:#6b4bb0;font-size:14px;padding:8px 16px;border-radius:12px;text-align:center;max-width:90%;}
.msg.bot{align-self:flex-start;display:flex;gap:10px;align-items:flex-start;}
.msg.bot .bubble{background:#eef0f5;color:var(--ink);padding:12px 16px;border-radius:14px;border-bottom-left-radius:4px;}
.msg.user{align-self:flex-end;background:linear-gradient(135deg,var(--blue-1),var(--blue-2));color:#fff;padding:12px 16px;border-radius:14px;border-bottom-right-radius:4px;}
.avatar{width:30px;height:30px;border-radius:9px;flex:0 0 auto;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--purple-1),var(--purple-2));}

.chat-input{display:flex;gap:10px;align-items:center;padding:14px;border-top:1px solid var(--line);background:#fafafe;}
#user-input{flex:1;padding:14px 16px;border:1px solid #ddd;border-radius:999px;font-size:16px;}
.mic-btn{width:52px;height:52px;border-radius:50%;border:none;cursor:pointer;font-size:20px;color:#fff;
  background:linear-gradient(135deg,var(--orange-1),var(--orange-2));box-shadow:0 0 0 3px var(--cream),0 6px 14px rgba(242,101,26,.3);}
.send-btn{min-height:52px;}

.chat-side{width:290px;flex:0 0 auto;display:flex;flex-direction:column;gap:10px;}
.side-label{font-family:monospace;font-size:12px;letter-spacing:1px;color:var(--muted);margin-bottom:4px;}
.quick-q{text-align:left;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-size:15px;
  color:var(--purple-2);cursor:pointer;box-shadow:0 4px 10px rgba(31,39,51,.05);}
.quick-q:hover{background:#faf7ff;}
.paalala{background:#fdf6e3;border:1px solid #f0e2b6;border-radius:14px;padding:16px;font-size:14px;color:#7a6320;margin-top:8px;}
.paalala-title{font-weight:700;margin-bottom:6px;}

@media (max-width:900px){
  .app-shell{flex-direction:column;}
  .rail{width:100%;flex-direction:row;align-items:center;overflow-x:auto;}
  .rail .brand{margin:0 16px 0 0;} .nav{flex-direction:row;} .rail-footer{flex-direction:row;margin:0 0 0 auto;}
  .hero{grid-template-columns:1fr;} .card-grid{grid-template-columns:1fr;} .hero-title{font-size:40px;}
  .chat-body{flex-direction:column;height:auto;} .chat-side{width:100%;} .messages{height:50vh;}
}
'''

# ------------------------------------------------------------
# static/script.js  (lang toggle + chat logic)
# ------------------------------------------------------------
script_js = '''// Language toggle (welcome screen)
document.querySelectorAll(".lang").forEach(function (btn) {
  btn.addEventListener("click", function () {
    document.querySelectorAll(".lang").forEach(function (b) { b.classList.remove("on"); });
    btn.classList.add("on");
  });
});

// ---------- Chat logic ----------
function addBubble(text, who) {
  const box = document.getElementById("messages");
  if (!box) return;
  const wrap = document.createElement("div");
  if (who === "bot") {
    wrap.className = "msg bot";
    wrap.innerHTML = '<span class="avatar"><svg viewBox="0 0 24 24" width="16" height="16" fill="none"><path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/></svg></span><div class="bubble"></div>';
    wrap.querySelector(".bubble").textContent = text;
  } else {
    wrap.className = "msg user";
    wrap.textContent = text;
  }
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
}

async function sendMessage(text) {
  const input = document.getElementById("user-input");
  const msg = (text || input.value).trim();
  if (!msg) return;
  addBubble(msg, "user");
  input.value = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    addBubble(data.reply, "bot");
  } catch (err) {
    addBubble("May error sa koneksyon sa server.", "bot");
  }
}

const sendBtn = document.getElementById("send-btn");
if (sendBtn) sendBtn.addEventListener("click", function () { sendMessage(); });

const inputBox = document.getElementById("user-input");
if (inputBox) inputBox.addEventListener("keydown", function (e) { if (e.key === "Enter") sendMessage(); });

document.querySelectorAll(".quick-q").forEach(function (btn) {
  btn.addEventListener("click", function () { sendMessage(btn.textContent); });
});

const micBtn = document.getElementById("mic-btn");
if (micBtn) micBtn.addEventListener("click", function () {
  addBubble("Ginagawa pa ang speech feature. Gamitin muna ang text sa ngayon.", "bot");
});
'''

files = {
    "main.py": main_py,
    "templates/chat.html": chat_html,
    "static/style.css": style_css,
    "static/script.js": script_js,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa/Inayos:", path)

print("\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Tapos: http://127.0.0.1:8000/chat")
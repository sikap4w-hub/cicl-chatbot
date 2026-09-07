import os
import json

# ============================================================
# Fullscreen booth game (TNMN-style, friendly). Isang laro,
# random na kaso (10 mabuti + 10 krimen). Instructions muna.
# 2 kaso kumpleto (modelo), 18 stub. Patakbuhin: python create_booth.py
# ============================================================

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("game_data", exist_ok=True)

# ------------------------------------------------------------
# game_data/cases.json
# ------------------------------------------------------------
cellphone = {
    "id": "cellphone", "type": "krimen", "status": "ready",
    "title": "Ang Cellphone sa Palengke", "caseno": "K-01",
    "bata": {"label": "Bata", "mood_start": "neutral"},
    "intro": "Kumusta po. Nahiram ko lang naman po kasi yung cellphone sa palengke, balak ko naman po sanang isauli.",
    "ebidensya": [
        {"label": "Testimonya ng tindera", "text": "Nakita kong kinuha ng bata ang phone sa mesa at umalis agad, walang nagpaalam kahit kanino."}
    ],
    "tanong": [
        {"q": "Kilala mo ba ang may-ari ng phone?", "sagot": "Hindi po... pero nasa mesa lang po siya, akala ko okay lang.", "mood": "kabado"},
        {"q": "Sino ang nagbigay ng pahintulot na kunin ito?", "sagot": "Wala po... pero balak ko naman po talagang isauli.", "mood": "malungkot"}
    ],
    "sugarcoat": {"phrase": "nahiram ko lang", "totoo": "kinuha nang walang pahintulot"},
    "tama_desisyon": "inspect",
    "pagbasa": [
        {"text": "Hiniram na may pahintulot ng may-ari", "tama": False},
        {"text": "Kinuha nang walang pahintulot", "tama": True}
    ],
    "resulta": {
        "tapat": "Ang totoo, kinuha ang phone nang walang paalam, na maaaring maituring na pagnanakaw.",
        "tamang_landas": "Sa ilalim ng RA 9344: kung labing-lima pababa, dadaan sa intervention; kung labing-anim hanggang labing-pito at may discernment, sa diversion. Layunin ay maituwid, hindi parusahan.",
        "tandaan": "Ang ganitong gawi ay hindi dapat tularan, ngunit laging may pagkakataong magbago at itama."
    },
    "aral": "Ang magagandang salita ay hindi nagbabago sa totoong nangyari."
}

pitaka = {
    "id": "pitaka", "type": "mabuti", "status": "ready",
    "title": "Ang Naibalik na Pitaka", "caseno": "M-01",
    "bata": {"label": "Bata", "mood_start": "kabado"},
    "intro": "Kumusta po. Nakakita po ako ng pitaka sa daan, dinala ko po agad sa barangay para maisauli sa may-ari.",
    "ebidensya": [
        {"label": "Testimonya ng barangay", "text": "Isinauli ng bata ang pitaka na buo ang laman at hinanap pa ang may-ari."}
    ],
    "tanong": [
        {"q": "Bakit mo dinala sa barangay?", "sagot": "Para po maibalik sa may-ari, baka po hinahanap nila.", "mood": "neutral"},
        {"q": "May kinuha ka bang laman?", "sagot": "Wala po, buo po lahat nang isinauli ko.", "mood": "ginhawa"}
    ],
    "tama_desisyon": "clear",
    "resulta": {
        "tapat": "Totoo ang kuwento, isinauli ng bata ang nahanap na pitaka nang buo.",
        "tamang_landas": "Ang ganitong katapatan ay dapat purihin at tularan.",
        "tandaan": "Mahalagang huwag agad humusga, may mga batang gumagawa ng tama."
    },
    "aral": "Huwag agad maghinala, kilalanin ang mabuting gawa."
}

crime_stubs = [
    ("away", "Ang Away sa Eskwelahan"), ("vandalismo", "Ang Pader na Sinulatan"),
    ("droga", "Ang Padalang Pakete"), ("inuman", "Ang Inuman sa Plaza"),
    ("cyberbully", "Ang Nakakahiyang Post"), ("armas", "Ang Dalang Patalim"),
    ("sugal", "Ang Online na Taya"), ("rambol", "Ang Sabwatan sa Labas"),
    ("holdap", "Ang Sapilitang Pagkuha")
]
good_stubs = [
    ("tumulong", "Ang Tumulong sa Nasugatan"), ("nagsabi", "Ang Nagsabi ng Totoo"),
    ("tumanggi", "Ang Tumanggi sa Barkada"), ("sukli", "Ang Isinauling Sukli"),
    ("nagreport", "Ang Nag-report ng Bully"), ("matanda", "Ang Tumulong sa Matanda"),
    ("nag-aral", "Ang Pinili ang Pag-aaral"), ("hayop", "Ang Nagligtas ng Hayop"),
    ("sumbong", "Ang Nagpaalam sa Nakita")
]

cases = [cellphone, pitaka]
for cid, title in crime_stubs:
    cases.append({"id": cid, "type": "krimen", "status": "soon", "title": title})
for cid, title in good_stubs:
    cases.append({"id": cid, "type": "mabuti", "status": "soon", "title": title})

with open("game_data/cases.json", "w", encoding="utf-8") as f:
    json.dump({"cases": cases}, f, indent=2, ensure_ascii=False)
print("Ginawa: game_data/cases.json (", len(cases), "kaso;", sum(1 for c in cases if c.get("status") == "ready"), "ready )")

# ------------------------------------------------------------
# main.py  (idinagdag: /laro fullscreen; /mga-kuwento -> redirect)
# ------------------------------------------------------------
main_py = '''import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE = Path(__file__).parent
app = FastAPI(title="Kaalaman at Karapatan")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def load_cases():
    with open(BASE / "game_data" / "cases.json", encoding="utf-8") as f:
        return json.load(f)["cases"]


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
# templates/booth.html  (standalone fullscreen, walang rail)
# ------------------------------------------------------------
booth_html = '''<!DOCTYPE html>
<html lang="tl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Laro - Kaalaman at Karapatan</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body class="booth-body">
  <div class="booth">
    <div class="booth-top">
      <button class="booth-exit" onclick="location.href='/menu'">&lsaquo; Umalis</button>
      <div class="booth-title">Ang Tulungan</div>
      <div class="booth-meta"><span id="progress">Kaso 0 ng 0</span> &middot; <span id="score">Puntos: 0</span></div>
    </div>

    <div class="booth-main">
      <div class="booth-left">
        <div class="case-card"><div class="case-no" id="case-no">--</div><div class="case-label">KASO</div></div>
        <div class="statement-paper" id="statement">Salaysay ng bata...</div>
        <div class="law-card"><b>RA 9344 gabay:</b> 15 pababa: intervention. 16-17 na may discernment: diversion. Layunin: tulong, hindi parusa.</div>
      </div>

      <div class="booth-center">
        <div class="screen-frame">
          <span class="bolt tl"></span><span class="bolt tr"></span><span class="bolt bl"></span><span class="bolt br"></span>
          <div id="character" class="character"></div>
        </div>
        <div id="dialogue" class="dialogue-box"></div>
      </div>

      <div class="booth-right">
        <div class="side-label">MGA DOKUMENTO</div>
        <div id="evidence-list"></div>
        <button class="phone-btn" id="phone-btn" title="Tawag para sa tulong">&#9742;</button>
      </div>
    </div>

    <div class="booth-actions" id="controls"></div>
  </div>

  <div id="modal" class="overlay">
    <div class="modal-card" id="modal-card">
      <h2>Paano Maglaro</h2>
      <ol class="instr-list">
        <li>Dumarating ang mga bata sa iyong desk, may dalang kuwento at dokumento.</li>
        <li>Makinig at magtanong. Pansinin kung tugma ang magagandang salita sa ebidensya.</li>
        <li>Piliin ang <b>Nauunawaan</b> kung malinaw at totoo, o <b>Suriin pa</b> kung may tinatago.</li>
        <li>Kung may mali, gagabayan mo ang bata sa tamang landas, hindi para husgahan kundi para tulungan.</li>
        <li>May puntos, ngunit ang pagkatuto ang mahalaga.</li>
      </ol>
      <button class="btn btn--blue" id="start-btn">Simulan</button>
    </div>
  </div>

  <script>window.CASES = {{ cases_json|safe }};</script>
  <script src="/static/booth.js"></script>
</body>
</html>
'''

# ------------------------------------------------------------
# static/booth.js
# ------------------------------------------------------------
booth_js = '''(function () {
  const CASES = (window.CASES || []).slice();
  // shuffle
  for (let i = CASES.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [CASES[i], CASES[j]] = [CASES[j], CASES[i]]; }

  const charEl = document.getElementById("character");
  const dialogueEl = document.getElementById("dialogue");
  const controlsEl = document.getElementById("controls");
  const evidenceEl = document.getElementById("evidence-list");
  const statementEl = document.getElementById("statement");
  const caseNoEl = document.getElementById("case-no");
  const progressEl = document.getElementById("progress");
  const scoreEl = document.getElementById("score");
  const modal = document.getElementById("modal");
  const modalCard = document.getElementById("modal-card");

  let idx = 0, score = 0;

  function face(mood) {
    const mouths = {
      neutral: '<path d="M50 74 h20" stroke="#5a4632" stroke-width="2.4" stroke-linecap="round"/>',
      kabado: '<path d="M50 74 q5 5 10 0 q5 -5 10 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M86 50 q4 6 0 10 q-4 -4 0 -10" fill="#7ec8ff"/>',
      malungkot: '<path d="M50 78 q10 -8 20 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/>',
      ginhawa: '<path d="M50 72 q10 9 20 0" stroke="#5a4632" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
    };
    const brows = {
      neutral: '<path d="M44 48 h10 M66 48 h10" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      kabado: '<path d="M44 46 l10 -2 M76 46 l-10 -2" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      malungkot: '<path d="M44 46 l10 2 M76 46 l-10 2" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>',
      ginhawa: '<path d="M44 47 h10 M66 47 h10" stroke="#5a4632" stroke-width="2.2" stroke-linecap="round"/>'
    };
    return '<svg viewBox="0 0 120 170" width="150" height="212">' +
      '<rect x="34" y="96" width="52" height="66" rx="14" fill="#7a3ff0"/>' +
      '<rect x="32" y="22" width="56" height="66" rx="26" fill="#f4c9a3"/>' +
      '<path d="M30 40 q30 -30 60 0 q-6 -18 -30 -18 q-24 0 -30 18z" fill="#3a2a1a"/>' +
      '<circle cx="52" cy="58" r="3.4" fill="#333"/><circle cx="68" cy="58" r="3.4" fill="#333"/>' +
      (brows[mood] || brows.neutral) + (mouths[mood] || mouths.neutral) + '</svg>';
  }
  function setMood(m) { charEl.innerHTML = face(m); charEl.classList.toggle("shake", m === "kabado"); }

  let typing = null;
  function typeText(text, cb) {
    if (typing) clearInterval(typing);
    dialogueEl.textContent = "";
    let i = 0;
    typing = setInterval(function () {
      dialogueEl.textContent += text.charAt(i); i++;
      if (i >= text.length) { clearInterval(typing); typing = null; if (cb) cb(); }
    }, 16);
  }
  function clearControls() { controlsEl.innerHTML = ""; }
  function addBtn(label, cls, onclick) {
    const b = document.createElement("button");
    b.className = cls; b.textContent = label;
    b.addEventListener("click", onclick); controlsEl.appendChild(b); return b;
  }
  function showModal(html) { modalCard.innerHTML = html; modal.classList.remove("hidden"); }
  function hideModal() { modal.classList.add("hidden"); }

  function updateHUD() {
    progressEl.textContent = "Kaso " + (idx + 1) + " ng " + CASES.length;
    scoreEl.textContent = "Puntos: " + score;
  }

  function loadCase(i) {
    const c = CASES[i];
    updateHUD();
    caseNoEl.textContent = c.caseno || "--";
    statementEl.innerHTML = '<b>Salaysay:</b> ' + (c.intro || "");
    charEl.style.transform = "translateX(-120%)";
    setMood(c.bata && c.bata.mood_start ? c.bata.mood_start : "neutral");
    setTimeout(function () { charEl.style.transition = "transform .6s ease"; charEl.style.transform = "translateX(0)"; }, 60);
    // evidence
    evidenceEl.innerHTML = "";
    (c.ebidensya || []).forEach(function (e) {
      const card = document.createElement("div");
      card.className = "evi-card";
      card.innerHTML = '<div class="evi-label">' + e.label + '</div><div class="evi-text">' + e.text + '</div>';
      evidenceEl.appendChild(card);
    });
    typeText(c.intro, function () { clearControls(); addBtn("Magtanong \\u203a", "btn btn--blue", function () { questioning(c); }); });
  }

  function questioning(c) {
    clearControls();
    (c.tanong || []).forEach(function (t) {
      const b = addBtn(t.q, "q-btn", function () { setMood(t.mood || "neutral"); typeText("\\u201c" + t.sagot + "\\u201d"); b.classList.add("asked"); });
    });
    addBtn("Handa na akong magpasya \\u203a", "btn btn--blue", function () { decision(c); });
  }

  function decision(c) {
    setMood("neutral"); clearControls();
    typeText("Batay sa kuwento at ebidensya, ano ang masasabi mo?", function () {
      addBtn("Nauunawaan", "btn btn--green", function () { judge(c, "clear"); });
      addBtn("Suriin pa", "btn btn--orange", function () { judge(c, "inspect"); });
    });
  }

  function judge(c, choice) {
    if (choice !== c.tama_desisyon) {
      clearControls();
      const hint = c.tama_desisyon === "inspect"
        ? "Mukhang may hindi pa tugma sa ebidensya. Suriin pa natin."
        : "Tila malinaw naman ang kuwento batay sa ebidensya. Balikan natin.";
      typeText(hint, function () { decision(c); });
      return;
    }
    if (c.tama_desisyon === "inspect") { reading(c); }
    else { score++; updateHUD(); resulta(c); }
  }

  function reading(c) {
    clearControls();
    typeText("Ano ang totoong nangyari, batay sa ebidensya?", function () {
      (c.pagbasa || []).forEach(function (opt) {
        addBtn(opt.text, "q-btn", function () {
          if (!opt.tama) { clearControls(); typeText("Tignan pa natin ang ebidensya. Subukan muli.", function () { reading(c); }); return; }
          score++; updateHUD(); resulta(c);
        });
      });
    });
  }

  function resulta(c) {
    setMood("ginhawa");
    const r = c.resulta || {};
    let html = '<h2>' + (c.type === "mabuti" ? "Mabuting Gawa" : "Pang-edukasyon na Resulta") + '</h2>';
    html += '<p><b>Ang totoo:</b> ' + (r.tapat || "") + '</p>';
    if (r.tamang_landas) html += '<p><b>Tamang landas:</b> ' + r.tamang_landas + '</p>';
    if (r.tandaan) html += '<div class="tandaan-box"><div class="tandaan-title">\\ud83d\\udee1 Mahalagang Tandaan</div><p>' + r.tandaan + '</p></div>';
    if (c.aral) html += '<p class="aral">\\u2728 ' + c.aral + '</p>';
    html += '<button class="btn btn--blue" id="next-btn">' + (idx + 1 < CASES.length ? "Susunod na Kaso \\u203a" : "Tapusin \\u203a") + '</button>';
    showModal(html);
    document.getElementById("next-btn").addEventListener("click", function () {
      hideModal(); idx++;
      if (idx < CASES.length) { charEl.style.transition = "none"; loadCase(idx); }
      else { showEnd(); }
    });
  }

  function showEnd() {
    let html = '<h2>Natapos ang Laro!</h2>';
    html += '<p>Natukoy mo nang tama ang <b>' + score + ' ng ' + CASES.length + '</b> na kaso.</p>';
    html += '<p>Higit sa puntos, ang mahalaga ay natutunan mong alamin ang totoo sa likod ng magagandang salita, at gabayan ang bata sa tamang paraan.</p>';
    html += '<button class="btn btn--blue" onclick="location.href=\\'/menu\\'">Bumalik sa Home</button>';
    showModal(html);
  }

  // Phone hint (placeholder)
  document.getElementById("phone-btn").addEventListener("click", function () {
    typeText("Payo: ihambing ang sinabi ng bata sa mga dokumento sa gilid.");
  });

  // Start button (instructions -> unang kaso)
  document.getElementById("start-btn").addEventListener("click", function () {
    if (!CASES.length) { showModal('<h2>Walang handang kaso</h2><p>Magdagdag ng ready na kaso sa cases.json.</p>'); return; }
    hideModal(); loadCase(0);
  });
})();
'''

# ------------------------------------------------------------
# static/style.css  (idagdag ang booth CSS)
# ------------------------------------------------------------
style_css = open("static/style.css", encoding="utf-8").read()

booth_css = '''

/* ---------- Fullscreen booth ---------- */
.booth-body{background:linear-gradient(135deg,#fff1e0,#ffe6ea);min-height:100vh;}
.booth{max-width:1180px;margin:0 auto;padding:16px;animation:boothIn .5s ease;}
@keyframes boothIn{from{opacity:0;transform:scale(.98);}to{opacity:1;transform:none;}}
.booth-top{display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.85);border-radius:14px;padding:12px 18px;margin-bottom:14px;box-shadow:0 6px 16px rgba(31,39,51,.08);}
.booth-exit{border:none;background:#fff;border-radius:999px;padding:9px 18px;cursor:pointer;font-size:15px;box-shadow:0 3px 8px rgba(31,39,51,.12);}
.booth-title{font-weight:800;font-size:20px;}
.booth-meta{font-size:14px;color:var(--muted);}
.booth-main{display:grid;grid-template-columns:230px 1fr 230px;gap:16px;align-items:start;}
.booth-left,.booth-right{display:flex;flex-direction:column;gap:12px;}
.case-card{background:#fff;border-radius:14px;padding:14px;text-align:center;box-shadow:var(--shadow);}
.case-no{font-size:24px;font-weight:800;letter-spacing:1px;color:var(--ink);}
.case-label{font-size:12px;color:var(--muted);letter-spacing:2px;}
.statement-paper,.law-card{background:#fffdf5;border:1px solid #efe6cf;border-radius:12px;padding:14px;font-size:14px;line-height:1.5;box-shadow:0 6px 14px rgba(31,39,51,.08);}
.statement-paper{transform:rotate(-1.2deg);}
.law-card{transform:rotate(1deg);color:#6b5a2a;}
.screen-frame{position:relative;border:10px solid #ffce8a;border-radius:22px;height:300px;overflow:hidden;
  background:linear-gradient(180deg,#e7f3ff 0%,#dbe9fb 70%,#cdba98 70%,#bda787 100%);
  display:flex;align-items:flex-end;justify-content:center;
  box-shadow:inset 0 4px 16px rgba(0,0,0,.08),0 10px 24px rgba(31,39,51,.12);}
.screen-frame .bolt{position:absolute;width:12px;height:12px;border-radius:50%;background:#e0a768;box-shadow:inset 0 -1px 2px rgba(0,0,0,.35);}
.bolt.tl{top:8px;left:8px;}.bolt.tr{top:8px;right:8px;}.bolt.bl{bottom:8px;left:8px;}.bolt.br{bottom:8px;right:8px;}
.booth-center .character{margin-bottom:26px;}
.booth-center .dialogue-box{margin-top:14px;min-height:70px;}
.phone-btn{width:52px;height:52px;border-radius:50%;border:none;cursor:pointer;color:#fff;font-size:22px;align-self:center;margin-top:6px;
  background:linear-gradient(135deg,var(--green-1),var(--green-2));box-shadow:0 6px 14px rgba(46,168,100,.3);}
.booth-actions{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:16px;background:rgba(255,255,255,.7);border-radius:14px;padding:14px;min-height:64px;}

.overlay{position:fixed;inset:0;background:rgba(20,20,30,.55);display:flex;align-items:center;justify-content:center;z-index:50;padding:20px;}
.overlay.hidden{display:none;}
.modal-card{background:#fff;border-radius:20px;padding:30px;max-width:560px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);max-height:88vh;overflow-y:auto;}
.modal-card h2{margin-bottom:14px;}
.modal-card p{margin-bottom:12px;line-height:1.6;}
.instr-list{margin:0 0 18px 20px;} .instr-list li{margin-bottom:8px;line-height:1.5;}
.aral{font-style:italic;color:var(--purple-2);}
@media (max-width:900px){ .booth-main{grid-template-columns:1fr;} }
'''

if "booth-main" not in style_css:
    style_css = style_css + booth_css

files = {
    "main.py": main_py,
    "templates/booth.html": booth_html,
    "static/booth.js": booth_js,
    "static/style.css": style_css,
}
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Ginawa/Inayos:", path)

print("\\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Subukan: http://127.0.0.1:8000/laro")
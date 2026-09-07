import os
import json

# ============================================================
# Idinadagdag ang suporta sa AI character art.
# - Gumagawa ng static/art/ folder
# - Nagdadagdag ng "art" field sa mga ready na kaso
# - Ginagawang image-aware ang engine (may placeholder fallback)
# Patakbuhin: python create_art_support.py
# ============================================================

os.makedirs("static/art", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("game_data", exist_ok=True)

# ------------------------------------------------------------
# static/art/READ_ME.txt
# ------------------------------------------------------------
readme = '''Ilagay dito ang mga AI character art (PNG, transparent background).

Naming: {bata}_{ekspresyon}.png
Ekspresyon: neutral, kabado, malungkot, ginhawa

Halimbawa:
  bata01_neutral.png
  bata01_kabado.png
  bata01_malungkot.png
  bata01_ginhawa.png

Kung wala pa ang file, placeholder na mukha muna ang lalabas.
Tingnan ang AI_Character_Art_Guide.md para sa prompts.
'''
with open("static/art/READ_ME.txt", "w", encoding="utf-8") as f:
    f.write(readme)
print("Ginawa: static/art/ (folder + READ_ME.txt)")

# ------------------------------------------------------------
# Dagdagan ng "art" field ang mga READY na kaso sa cases.json
# ------------------------------------------------------------
with open("game_data/cases.json", encoding="utf-8") as f:
    data = json.load(f)

n = 0
for c in data["cases"]:
    if c.get("status") == "ready":
        n += 1
        c.setdefault("bata", {})
        c["bata"].setdefault("art", "bata%02d" % n)  # bata01, bata02, ...

with open("game_data/cases.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Inayos: cases.json (nadagdagan ng art field ang", n, "ready na kaso)")

# ------------------------------------------------------------
# Palitan ang booth.js ng image-aware na bersyon
# ------------------------------------------------------------
booth_js = '''(function () {
  const CASES = (window.CASES || []).slice();
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

  let idx = 0, score = 0, currentCase = null;

  // ----- Placeholder na mukha (fallback kapag walang art file) -----
  function phFace(mood) {
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

  // ----- setMood: subukan ang totoong art; kung wala, placeholder -----
  function setMood(mood) {
    charEl.classList.toggle("shake", mood === "kabado");
    const art = currentCase && currentCase.bata && currentCase.bata.art;
    if (!art) { charEl.innerHTML = phFace(mood); return; }
    const img = new Image();
    img.className = "char-img";
    img.alt = "";
    img.onload = function () { charEl.innerHTML = ""; charEl.appendChild(img); };
    img.onerror = function () { charEl.innerHTML = phFace(mood); };
    img.src = "/static/art/" + art + "_" + mood + ".png";
  }

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
    const c = CASES[i]; currentCase = c;
    updateHUD();
    caseNoEl.textContent = c.caseno || "--";
    statementEl.innerHTML = '<b>Salaysay:</b> ' + (c.intro || "");
    charEl.style.transition = "none";
    charEl.style.transform = "translateX(-120%)";
    setMood(c.bata && c.bata.mood_start ? c.bata.mood_start : "neutral");
    setTimeout(function () { charEl.style.transition = "transform .6s ease"; charEl.style.transform = "translateX(0)"; }, 60);
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
      if (idx < CASES.length) { loadCase(idx); } else { showEnd(); }
    });
  }

  function showEnd() {
    let html = '<h2>Natapos ang Laro!</h2>';
    html += '<p>Natukoy mo nang tama ang <b>' + score + ' ng ' + CASES.length + '</b> na kaso.</p>';
    html += '<p>Higit sa puntos, ang mahalaga ay natutunan mong alamin ang totoo sa likod ng magagandang salita, at gabayan ang bata sa tamang paraan.</p>';
    html += '<button class="btn btn--blue" onclick="location.href=\\'/menu\\'">Bumalik sa Home</button>';
    showModal(html);
  }

  document.getElementById("phone-btn").addEventListener("click", function () {
    typeText("Payo: ihambing ang sinabi ng bata sa mga dokumento sa gilid.");
  });

  document.getElementById("start-btn").addEventListener("click", function () {
    if (!CASES.length) { showModal('<h2>Walang handang kaso</h2><p>Magdagdag ng ready na kaso sa cases.json.</p>'); return; }
    hideModal(); loadCase(0);
  });

  window.__phFace = phFace;
})();
'''

with open("static/booth.js", "w", encoding="utf-8") as f:
    f.write(booth_js)
print("Inayos: static/booth.js (image-aware na, may fallback)")

# ------------------------------------------------------------
# Idagdag ang .char-img CSS
# ------------------------------------------------------------
style_css = open("static/style.css", encoding="utf-8").read()
if ".char-img" not in style_css:
    style_css += '''

/* ---------- Character art image ---------- */
.char-img{height:220px;width:auto;max-width:200px;object-fit:contain;display:block;}
'''
    with open("static/style.css", "w", encoding="utf-8") as f:
        f.write(style_css)
    print("Inayos: static/style.css (dinagdag ang .char-img)")

print("\\nTapos na! Patakbuhin ulit: uvicorn main:app --reload")
print("Ilagay ang art sa static/art/ (hal. bata01_neutral.png), tapos i-refresh ang /laro")
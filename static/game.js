(function () {
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
      addBtn("Magtanong \u203a", "btn btn--blue", startQuestioning);
    });
  }

  const asked = {};
  function startQuestioning() {
    renderEvidence();
    clearControls();
    (CASE.tanong || []).forEach(function (t, i) {
      const b = addBtn(t.q, "q-btn", function () { askQuestion(i, b); });
    });
    addBtn("Handa na akong magpasya \u203a", "btn btn--blue", startVerdict);
  }
  function askQuestion(i, btn) {
    const t = CASE.tanong[i];
    setMood(t.mood || "neutral");
    typeText("\u201c" + t.sagot + "\u201d");
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
    let html = '<div class="result-badge">\u24d8 Pang-edukasyon na resulta</div>';
    html += '<div class="result-box"><p class="result-text"><b>Ang totoo:</b> ' + (r.tapat || "") + '</p>';
    if (r.bakit) html += '<p class="result-text">' + r.bakit + '</p>';
    if (r.tamang_landas) html += '<p class="result-text"><b>Tamang landas:</b> ' + r.tamang_landas + '</p>';
    html += '</div>';
    if (r.huwag_tularan) html += '<div class="tandaan-box"><div class="tandaan-title">\ud83d\udee1 Mahalagang Tandaan</div><p>' + r.huwag_tularan + '</p></div>';
    html += '<div class="result-actions"><a href="/kuwento/' + CASE.id + '/tapos" class="btn btn--blue">Magpatuloy \u203a</a>' +
            '<a href="/kuwento/' + CASE.id + '" class="btn btn--ghost">Ulitin</a></div>';
    sceneMain.innerHTML = html;
  }

  startIntro();
})();

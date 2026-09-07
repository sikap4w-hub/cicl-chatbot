(function () {
  const CASES = (window.CASES || []).slice();
  for (let i = CASES.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [CASES[i], CASES[j]] = [CASES[j], CASES[i]]; }

  const stageEl = document.getElementById("char-stage");
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

  const docsPanel = document.getElementById("docs-panel");
  const docsClose = document.getElementById("docs-close");
  const folderBtn = document.getElementById("folder-btn");
  const callPanel = document.getElementById("call-panel");
  const callClose = document.getElementById("call-close");
  const callDialogueEl = document.getElementById("call-dialogue");
  const callControlsEl = document.getElementById("call-controls");

  let idx = 0, score = 0, currentCase = null, started = false;

  // ============================================================
  // SESSION PROGRESS
  // Gamit ang sessionStorage (hindi localStorage) para ang progreso ay
  // manatili habang lumilipat ka sa ibang parte ng site (hal. chat) at
  // bumalik, pero mag-reset kapag ni-refresh ang mismong pahina ng laro.
  // Para makilala ang totoong refresh laban sa normal na pagbalik/navigation,
  // ginagamit ang Navigation Timing API.
  // ============================================================
  const STORAGE_KEY = "cicl_game_state";

  function isPageReload() {
    try {
      const nav = performance.getEntriesByType && performance.getEntriesByType("navigation")[0];
      if (nav) return nav.type === "reload";
      if (performance.navigation) return performance.navigation.type === 1;
    } catch (e) { /* ignore */ }
    return false;
  }

  function saveState() {
    if (!started) return;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        order: CASES.map(function (c) { return c.caseno; }),
        idx: idx,
        score: score
      }));
    } catch (e) { /* sessionStorage unavailable -- ok lang, wala lang progress save */ }
  }

  function clearState() {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
  }

  if (isPageReload()) clearState();

  let resumed = false;
  if (!isPageReload()) {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      const saved = raw && JSON.parse(raw);
      if (saved && Array.isArray(saved.order) && saved.order.length === CASES.length &&
          typeof saved.idx === "number" && saved.idx >= 0 && saved.idx < CASES.length) {
        const byNo = {};
        CASES.forEach(function (c) { byNo[c.caseno] = c; });
        const reordered = saved.order.map(function (no) { return byNo[no]; });
        if (reordered.every(Boolean)) {
          CASES.length = 0;
          Array.prototype.push.apply(CASES, reordered);
          idx = saved.idx;
          score = saved.score || 0;
          started = true;
          resumed = true;
        }
      }
    } catch (e) { /* wala lang, magsisimula na lang tayo mula sa simula */ }
  }

  // ============================================================
  // CHROME I18N
  // Ang mga sumusunod na string ay bahagi ng "makina" ng laro (buttons,
  // HUD, hints) -- hindi ito kwento ng partikular na kaso, kaya ligtas
  // itong i-translate. Ang aktwal na kwento/tanong/resulta ng bawat kaso
  // (galing sa cases.json) ay Tagalog pa rin, sadya, dahil doon
  // nakasalalay ang buong laro.
  // ============================================================
  const CHROME = {
    tl: {
      caseOf: function (n, total) { return "Kaso " + n + " ng " + total; },
      points: function (n) { return "Puntos: " + n; },
      askQuestions: "Magtanong ›",
      readyToDecide: "Handa na akong magpasya ›",
      decidePrompt: "Batay sa kuwento at ebidensya, ano ang masasabi mo?",
      truthful: "Nagsasabi ng Totoo",
      mismatch: "Hindi Tugma ang Kwento",
      hintInspect: "Mukhang may hindi pa tugma sa ebidensya. Suriin pa natin.",
      hintClear: "Tila malinaw naman ang kuwento batay sa ebidensya. Balikan natin.",
      readingPrompt: "Ano ang totoong nangyari, batay sa ebidensya?",
      readingRetry: "Tignan pa natin ang ebidensya. Subukan muli.",
      goodDeed: "Mabuting Gawa",
      lessonResult: "Pang-edukasyon na Resulta",
      truthLabel: "Ang totoo:",
      pathLabel: "Tamang landas:",
      reminderTitle: "🛡 Mahalagang Tandaan",
      nextCase: "Susunod na Kaso ›",
      finish: "Tapusin ›",
      gameOver: "Natapos ang Laro!",
      gameOverScore: function (score, total) { return "Natukoy mo nang tama ang <b>" + score + " ng " + total + "</b> na kaso."; },
      gameOverNote: "Higit sa puntos, ang mahalaga ay natutunan mong alamin ang totoo sa likod ng magagandang salita, at gabayan ang bata sa tamang paraan.",
      backHome: "Bumalik sa Home",
      noParentInfo: "Wala pang available na impormasyon mula sa magulang para sa kasong ito.",
      noActiveCase: "Wala pang aktibong kaso.",
      callGreeting: "Kumusta po. Ito po ang barangay tanggapan, gusto ko lang po itanong tungkol sa anak niyo.",
      noReadyCases: "Walang handang kaso",
      noReadyCasesNote: "Magdagdag ng ready na kaso sa cases.json."
    },
    en: {
      caseOf: function (n, total) { return "Case " + n + " of " + total; },
      points: function (n) { return "Points: " + n; },
      askQuestions: "Ask questions ›",
      readyToDecide: "I'm ready to decide ›",
      decidePrompt: "Based on the story and the evidence, what's your call?",
      truthful: "Nagsasabi ng Totoo",
      mismatch: "Hindi Tugma ang Kwento",
      hintInspect: "Something still doesn't match the evidence. Let's look closer.",
      hintClear: "The story actually looks clear based on the evidence. Let's go back.",
      readingPrompt: "What actually happened, based on the evidence?",
      readingRetry: "Let's look at the evidence again. Try once more.",
      goodDeed: "Good Deed",
      lessonResult: "Learning Outcome",
      truthLabel: "What actually happened:",
      pathLabel: "The right path:",
      reminderTitle: "🛡 Important Reminder",
      nextCase: "Next Case ›",
      finish: "Finish ›",
      gameOver: "Game Complete!",
      gameOverScore: function (score, total) { return "You correctly identified <b>" + score + " of " + total + "</b> cases."; },
      gameOverNote: "More than the score, what matters is that you learned to look past nice-sounding words to find the truth, and to guide the child the right way.",
      backHome: "Back to Home",
      noParentInfo: "No information from the parent is available yet for this case.",
      noActiveCase: "No active case yet.",
      callGreeting: "Kumusta po. Ito po ang barangay tanggapan, gusto ko lang po itanong tungkol sa anak niyo.",
      noReadyCases: "No case is ready yet",
      noReadyCasesNote: "Add a case with status \"ready\" in cases.json."
    }
  };
  function t(key) {
    const lang = (window.ciclLang && window.ciclLang.get() === "en") ? "en" : "tl";
    return CHROME[lang][key];
  }

  // ============================================================
  // CHARACTER ART
  // Files: /static/art/{bata}_{mood}.png  (transparent PNG)
  // Moods: neutral, kabado, malungkot, ginhawa
  // Fallback: hiniling na mood -> neutral -> placeholder SVG
  // ============================================================
  const MOODS = ["neutral", "kabado", "malungkot", "ginhawa"];
  const artStatus = Object.create(null);   // src -> "ok" | "fail" | "loading"

  // Ang mga art file ay naka-save gamit ang Ingles na pangalan
  // (nervous / sad / relieved) habang Tagalog ang mood key sa laro.
  // Dito ibinabagay ang isa sa isa.
  const MOOD_FILE = { neutral: "neutral", kabado: "nervous", malungkot: "sad", ginhawa: "relieved" };
  function artSrc(key, mood) { return "/static/art/" + key + "_" + (MOOD_FILE[mood] || mood) + ".png"; }

  // Ihanda ang lahat ng mood ng isang kaso bago pa ito lumabas sa screen.
  function preloadCase(c) {
    const key = c && c.bata && c.bata.art;
    if (!key) return;
    MOODS.forEach(function (m) {
      const src = artSrc(key, m);
      if (artStatus[src]) return;
      artStatus[src] = "loading";
      const im = new Image();
      im.decoding = "async";
      im.addEventListener("load", function () { artStatus[src] = "ok"; });
      im.addEventListener("error", function () { artStatus[src] = "fail"; });
      im.src = src;
    });
  }

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

  function placeholderNode(mood) {
    const d = document.createElement("div");
    d.className = "char-layer char-ph";
    d.innerHTML = phFace(mood);
    return d;
  }

  function imgNode(src) {
    const im = new Image();
    im.className = "char-layer char-img";
    im.alt = "";
    im.src = src;
    return im;
  }

  // Palitan ang nakikitang layer, may crossfade (walang flicker).
  function swapLayer(node) {
    const old = charEl.querySelector(".char-layer.is-on");
    charEl.appendChild(node);
    void node.offsetWidth;                 // reflow para tumakbo ang transition
    node.classList.add("is-on");
    if (old && old !== node) {
      old.classList.remove("is-on");
      setTimeout(function () { if (old.parentNode === charEl) charEl.removeChild(old); }, 300);
    }
  }

  let moodToken = 0;
  function setMood(mood) {
    if (MOODS.indexOf(mood) === -1) mood = "neutral";
    charEl.classList.toggle("shake", mood === "kabado");

    const key = currentCase && currentCase.bata && currentCase.bata.art;
    const token = ++moodToken;

    if (!key) { swapLayer(placeholderNode(mood)); return; }

    const chain = (mood === "neutral") ? [mood] : [mood, "neutral"];

    (function tryNext(i) {
      if (token !== moodToken) return;      // may mas bagong setMood na tumakbo
      if (i >= chain.length) { swapLayer(placeholderNode(mood)); return; }
      const src = artSrc(key, chain[i]);
      const st = artStatus[src];

      if (st === "ok") { swapLayer(imgNode(src)); return; }
      if (st === "fail") { tryNext(i + 1); return; }

      // Hindi pa tapos mag-load: hintayin bago magpasya.
      const probe = new Image();
      probe.addEventListener("load", function () {
        artStatus[src] = "ok";
        if (token !== moodToken) return;
        swapLayer(imgNode(src));
      });
      probe.addEventListener("error", function () { artStatus[src] = "fail"; tryNext(i + 1); });
      probe.src = src;
    })(0);
  }

  // ============================================================
  // DIALOGUE / UI
  // ============================================================
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
    progressEl.textContent = t("caseOf")(idx + 1, CASES.length);
    scoreEl.textContent = t("points")(score);
    saveState();
  }
  document.addEventListener("cicl:langchange", updateHUD);

  function loadCase(i) {
    const c = CASES[i]; currentCase = c;
    closePanels();
    updateHUD();
    caseNoEl.textContent = c.caseno || "--";
    statementEl.innerHTML = '<b>Salaysay:</b> ' + (c.intro || "");

    // Parang naglalakad ang bata papalapit mula sa hallway: maliit at
    // malabo muna, tapos lumalaki at lumilinaw sa loob ng ~3 segundo.
    // Gumagamit ng class (hindi inline transform) para hindi masira ang
    // pag-center ng .char-stage na naka-CSS (translateX(-50%)).
    stageEl.classList.add("no-anim", "walk-in");
    void stageEl.offsetWidth;             // reflow bago tanggalin ang no-anim
    charEl.innerHTML = "";
    setMood(c.bata && c.bata.mood_start ? c.bata.mood_start : "neutral");
    setTimeout(function () {
      stageEl.classList.remove("no-anim");
      stageEl.classList.remove("walk-in");
    }, 60);

    evidenceEl.innerHTML = "";
    (c.ebidensya || []).forEach(function (e) {
      const card = document.createElement("div");
      card.className = "evi-card";
      card.innerHTML = '<div class="evi-label">' + e.label + '</div><div class="evi-text">' + e.text + '</div>';
      evidenceEl.appendChild(card);
    });

    if (CASES[i + 1]) preloadCase(CASES[i + 1]);   // ihanda na ang susunod na bata

    typeText(c.intro, function () { clearControls(); addBtn(t("askQuestions"), "btn btn--blue", function () { questioning(c); }); });
  }

  function questioning(c) {
    clearControls();
    (c.tanong || []).forEach(function (q) {
      const b = addBtn(q.q, "q-btn", function () { setMood(q.mood || "neutral"); typeText("“" + q.sagot + "”"); b.classList.add("asked"); });
    });
    addBtn(t("readyToDecide"), "btn btn--blue", function () { decision(c); });
  }

  // Ilang segundong hintay bago magpatuloy, para may oras na mabasa
  // ang huling sinabi bago ito mapalitan ng susunod na tanong.
  const READ_PAUSE_MS = 1800;

  function decision(c) {
    setMood("neutral"); clearControls();
    typeText(t("decidePrompt"), function () {
      addBtn(t("truthful"), "btn btn--green", function () { judge(c, "clear"); });
      addBtn(t("mismatch"), "btn btn--orange", function () { judge(c, "inspect"); });
    });
  }

  function judge(c, choice) {
    if (choice !== c.tama_desisyon) {
      clearControls();
      setMood("kabado");
      const hint = c.tama_desisyon === "inspect" ? t("hintInspect") : t("hintClear");
      typeText(hint, function () { setTimeout(function () { decision(c); }, READ_PAUSE_MS); });
      return;
    }
    if (c.tama_desisyon === "inspect") { reading(c); }
    else { score++; updateHUD(); resulta(c); }
  }

  function reading(c) {
    clearControls();
    setMood("malungkot");
    typeText(t("readingPrompt"), function () {
      (c.pagbasa || []).forEach(function (opt) {
        addBtn(opt.text, "q-btn", function () {
          if (!opt.tama) {
            clearControls();
            typeText(t("readingRetry"), function () { setTimeout(function () { reading(c); }, READ_PAUSE_MS); });
            return;
          }
          score++; updateHUD(); resulta(c);
        });
      });
    });
  }

  function resulta(c) {
    setMood("ginhawa");
    const r = c.resulta || {};
    let html = '<h2>' + (c.type === "mabuti" ? t("goodDeed") : t("lessonResult")) + '</h2>';
    html += '<p><b>' + t("truthLabel") + '</b> ' + (r.tapat || "") + '</p>';
    if (r.tamang_landas) html += '<p><b>' + t("pathLabel") + '</b> ' + r.tamang_landas + '</p>';
    if (r.tandaan) html += '<div class="tandaan-box"><div class="tandaan-title">' + t("reminderTitle") + '</div><p>' + r.tandaan + '</p></div>';
    if (c.aral) html += '<p class="aral">✨ ' + c.aral + '</p>';
    html += '<button class="btn btn--blue" id="next-btn">' + (idx + 1 < CASES.length ? t("nextCase") : t("finish")) + '</button>';
    showModal(html);
    document.getElementById("next-btn").addEventListener("click", function () {
      hideModal(); idx++;
      if (idx < CASES.length) { loadCase(idx); } else { showEnd(); }
    });
  }

  function showEnd() {
    clearState();
    let html = '<h2>' + t("gameOver") + '</h2>';
    html += '<p>' + t("gameOverScore")(score, CASES.length) + '</p>';
    html += '<p>' + t("gameOverNote") + '</p>';
    html += '<button class="btn btn--blue" onclick="location.href=\'/menu\'">' + t("backHome") + '</button>';
    showModal(html);
  }

  // ============================================================
  // PANELS: mga dokumento (folder) at tawag sa magulang (phone)
  // ============================================================
  function openPanel(panel) {
    docsPanel.classList.add("hidden");
    callPanel.classList.add("hidden");
    panel.classList.remove("hidden");
  }
  function closePanels() {
    docsPanel.classList.add("hidden");
    callPanel.classList.add("hidden");
  }

  function renderCallOptions() {
    callControlsEl.innerHTML = "";
    const list = (currentCase && currentCase.tawag_magulang) || [];
    if (!list.length) {
      const p = document.createElement("p");
      p.textContent = t("noParentInfo");
      callControlsEl.appendChild(p);
      return;
    }
    list.forEach(function (qa) {
      const b = document.createElement("button");
      b.className = "q-btn";
      b.textContent = qa.tanong;
      b.addEventListener("click", function () {
        callDialogueEl.textContent = "“" + qa.sagot + "”";
        b.classList.add("asked");
      });
      callControlsEl.appendChild(b);
    });
  }

  folderBtn.addEventListener("click", function () { openPanel(docsPanel); });
  docsClose.addEventListener("click", closePanels);

  document.getElementById("phone-btn").addEventListener("click", function () {
    callDialogueEl.textContent = currentCase ? t("callGreeting") : t("noActiveCase");
    renderCallOptions();
    openPanel(callPanel);
  });
  callClose.addEventListener("click", closePanels);

  document.getElementById("start-btn").addEventListener("click", function () {
    if (!CASES.length) { showModal('<h2>' + t("noReadyCases") + '</h2><p>' + t("noReadyCasesNote") + '</p>'); return; }
    started = true;
    hideModal(); loadCase(0);
  });

  // Habang binabasa pa ang instruksiyon, i-preload na ang unang bata.
  if (CASES[0]) preloadCase(CASES[0]);

  // May naka-save na progreso mula sa parehong tab session (hindi galing sa
  // refresh) -- ituloy agad sa kasalukuyang kaso sa halip na ipakita ulit
  // ang panimulang instructions modal.
  if (resumed) { hideModal(); loadCase(idx); }

  window.__phFace = phFace;
  window.__artStatus = artStatus;
})();

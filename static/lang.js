// lang.js - Shared Filipino/English toggle para sa buong site.
//
// Paano gamitin sa isang template:
//   1. Lagyan ng data-tl="..." at data-en="..." ang element (textContent swap),
//      o data-tl-html/data-en-html kung may kailangang HTML markup sa loob,
//      o data-tl-placeholder/data-en-placeholder para sa <input placeholder>,
//      o data-tl-title/data-en-title para sa title tooltip.
//   2. Lagyan ng class="lang-fade" ang mga container na gustong mag-crossfade
//      habang nagbabago ang wika (opsyonal, pero mas maganda ang transition).
//   3. Gumawa ng button(s) na may data-lang-btn="tl" / data-lang-btn="en".
//   4. I-include ang <script src="/static/lang.js"></script>.
//
// Ang napiling wika ay naka-imbak sa localStorage ("cicl-lang") kaya
// nananatili ito kahit magpalipat-lipat ng page.
(function () {
  var STORAGE_KEY = "cicl-lang";
  var FADE_MS = 180;

  function getLang() {
    try { return localStorage.getItem(STORAGE_KEY) || "tl"; } catch (e) { return "tl"; }
  }
  function setLang(lang) {
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
  }

  function swapText(lang) {
    var sel = "[data-tl],[data-tl-html],[data-tl-placeholder],[data-tl-title]";
    document.querySelectorAll(sel).forEach(function (el) {
      var text = lang === "en" ? el.getAttribute("data-en") : el.getAttribute("data-tl");
      var html = lang === "en" ? el.getAttribute("data-en-html") : el.getAttribute("data-tl-html");
      var ph = lang === "en" ? el.getAttribute("data-en-placeholder") : el.getAttribute("data-tl-placeholder");
      var title = lang === "en" ? el.getAttribute("data-en-title") : el.getAttribute("data-tl-title");
      if (html !== null) el.innerHTML = html;
      else if (text !== null) el.textContent = text;
      if (ph !== null) el.setAttribute("placeholder", ph);
      if (title !== null) el.setAttribute("title", title);
    });
    document.documentElement.setAttribute("lang", lang === "en" ? "en" : "tl");
  }

  function applyLang(lang, animate) {
    document.querySelectorAll("[data-lang-btn]").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-lang-btn") === lang);
    });
    setLang(lang);

    var fadeEls = document.querySelectorAll(".lang-fade");
    var finish = function () {
      swapText(lang);
      document.dispatchEvent(new CustomEvent("cicl:langchange", { detail: { lang: lang } }));
    };
    if (!animate || !fadeEls.length) { finish(); return; }
    fadeEls.forEach(function (el) { el.classList.add("fading"); });
    setTimeout(function () {
      finish();
      fadeEls.forEach(function (el) { el.classList.remove("fading"); });
    }, FADE_MS);
  }

  function init() {
    document.querySelectorAll("[data-lang-btn]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyLang(btn.getAttribute("data-lang-btn"), true);
      });
    });
    applyLang(getLang(), false);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.ciclLang = { get: getLang, apply: applyLang };
})();

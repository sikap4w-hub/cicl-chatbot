// Note: ang Filipino/English toggle ay hawak na ng /static/lang.js (shared
// sa buong site). Dati dito ito ginagawa pero pinalitan na.

// ---------- Chat logic ----------
// Bawat bagong bubble (.msg) ay may CSS animation (msg-in, sa style.css) na
// awtomatikong tumatakbo sa sandaling idagdag ito sa DOM, kaya hindi na ito
// bigla na lang lumalabas.
function addBubble(text, who, citations) {
  const box = document.getElementById("messages");
  if (!box) return null;
  const wrap = document.createElement("div");
  if (who === "bot") {
    wrap.className = "msg bot";
    wrap.innerHTML = '<span class="avatar"><svg viewBox="0 0 24 24" width="16" height="16" fill="none"><path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/></svg></span>' +
      '<div class="bot-content"><div class="bubble"></div><div class="msg-citations"></div></div>';
    // Bot replies galing sa sarili nating intents.json (hindi mula sa
    // user), kaya ligtas gamitin ang innerHTML -- dito ginagamit ang mga
    // <br> at bullet ("•") sa laman ng sagot para maging structured at
    // madaling basahin ng bata, sa halip na isang mahabang parapo.
    wrap.querySelector(".bubble").innerHTML = text;
    // Mga citation (hal. "RA 9344, Sec. 6") -- inilalagay sa LABAS ng
    // bubble, nasa kanang-kanan, maliit at italicized na font, para
    // makita ng user kung saang bahagi ng batas nagmula ang sagot nang
    // hindi ito nakakasagabal sa pangunahing teksto ng sagot mismo.
    if (citations && citations.length) {
      wrap.querySelector(".msg-citations").textContent = citations.join(" • ");
    }
  } else {
    wrap.className = "msg user";
    wrap.textContent = text;
  }
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
  return wrap;
}

// Ipinapakita ang sagot ng bot nang paunti-unti (parang "typing"), sa halip
// na biglang lumabas ang buong sagot nang sabay -- pakiramdam nito ay
// parang aktwal na may kausap, hindi lang basta text na sumulpot.
// Ang mga HTML tag (<br>, <i>, atbp., mula sa normalize_formatting sa
// backend) ay ini-insert nang buo agad (hindi ini-type letra-letra), pero
// ang mga salita sa pagitan ng mga tag ay lumalabas nang isa-isa.
// BUG na naayos dito: ang lumang bersyon ay `insertAdjacentHTML`-inseinsert
// ang bawat tag TOKEN nang HIWALAY sa bawat isa (hal. "<span ...>" tapos
// mamaya lang, pagkatapos ng ilang text node, ang "</span>"). Pero kapag
// binigyan ng browser ng ISANG bukas na tag lang na walang kasamang
// closing tag, awtomatiko itong ini-close ng parser bilang EMPTY na
// element -- kaya ang sumusunod na text ay hindi na talaga naka-nest sa
// loob ng span/i, kundi bilang karugtong na sibling na text node lang sa
// bubbleEl mismo. Resulta: mukhang "gumagana" ang code (walang error),
// pero anumang CSS class na naka-attach sa span/i (tulad ng disclaimer
// styling) ay WALANG EPEKTO dahil walang laman ang element na iyon.
//
// Ayos dito: mag-iingat ng isang STACK ng mga currently-open na element.
// Ang "container" ay laging ang taas ng stack (o ang bubbleEl kung wala
// pang bukas na tag) -- doon idinaragdag ang bawat susunod na text node
// o bagong child element, kaya tama ang pagkaka-nest.
function typeBubble(bubbleEl, html, onDone) {
  const TYPE_SPEED_MS = 22; // bilis ng bawat salita
  const VOID_TAGS = new Set(["br", "img", "hr", "input"]);
  const tokens = html.match(/<[^>]+>|[^<]+/g) || [html];
  const stack = [bubbleEl];
  let ti = 0;

  function currentContainer() {
    return stack[stack.length - 1];
  }

  function nextTag() {
    while (ti < tokens.length && tokens[ti].charAt(0) === "<") {
      const tag = tokens[ti];
      const closeMatch = tag.match(/^<\/\s*([a-zA-Z0-9]+)/);
      const openMatch = tag.match(/^<\s*([a-zA-Z0-9]+)/);
      if (closeMatch) {
        // Pop lang -- huwag bumaba pa sa ibaba ng bubbleEl mismo (index 0).
        if (stack.length > 1) stack.pop();
      } else if (openMatch && !tag.endsWith("/>") && !VOID_TAGS.has(openMatch[1].toLowerCase())) {
        // Gumawa ng aktwal na element (hindi text) mula sa tag string, tapos
        // itulak sa stack bilang bagong "current container" para dito
        // idagdag ang susunod na mga text node/child.
        const wrapper = document.createElement("div");
        wrapper.innerHTML = tag + "</" + openMatch[1] + ">";
        const el = wrapper.firstChild;
        if (el) {
          currentContainer().appendChild(el);
          stack.push(el);
        }
      } else {
        // Void/self-closing na tag (hal. <br>) -- idagdag lang, walang push.
        currentContainer().insertAdjacentHTML("beforeend", tag);
      }
      ti++;
    }
    if (ti >= tokens.length) {
      if (onDone) onDone();
      return;
    }
    typeTextChunk(tokens[ti]);
  }

  function typeTextChunk(chunk) {
    const words = chunk.split(/(\s+)/).filter(function (w) { return w.length > 0; });
    let wi = 0;
    (function step() {
      if (wi >= words.length) {
        ti++;
        nextTag();
        return;
      }
      currentContainer().appendChild(document.createTextNode(words[wi]));
      wi++;
      const box = document.getElementById("messages");
      if (box) box.scrollTop = box.scrollHeight;
      setTimeout(step, TYPE_SPEED_MS);
    })();
  }

  nextTag();
}

// "Nagta-type pa..." na tatlong tumatalon na tuldok, habang hinihintay ang
// sagot ng backend -- para maramdaman ng bata na may kausap talaga siya,
// hindi lang bigla na lang lumalabas ang sagot.
function showTyping() {
  const box = document.getElementById("messages");
  if (!box) return null;
  const wrap = document.createElement("div");
  wrap.className = "msg bot typing";
  wrap.innerHTML = '<span class="avatar"><svg viewBox="0 0 24 24" width="16" height="16" fill="none"><path d="M12 3l7 2.5v5C19 15 15.7 18.5 12 20 8.3 18.5 5 15 5 10.5v-5L12 3z" fill="#fff"/></svg></span>' +
    '<div class="bubble"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>';
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
  return wrap;
}

const MIN_TYPING_MS = 500; // para hindi kumurap-kurap lang agad ang typing dots

async function sendMessage(text) {
  const input = document.getElementById("user-input");
  const msg = (text || input.value).trim();
  if (!msg) return;
  // Ipinapadala ang huling ilang turn NG PAREHONG session (bago pa idagdag
  // ang bagong mensahe) kasama ang request, para may context ang backend
  // para sa mga follow-up na tanong (hal. "ano connect nito sakin"). Walang
  // server-side session storage sa backend na ito -- ang chatLog na
  // naka-persist na sa sessionStorage (tingnan sa itaas) mismo ang
  // "memorya", kaya sapat nang ipasa ito sa bawat request.
  const historyToSend = chatLog.slice(-6).map(function (e) {
    return { who: e.who, text: e.text };
  });

  addBubble(msg, "user");
  chatLog.push({ who: "user", text: msg });
  saveChatState();
  input.value = "";
  const typingEl = showTyping();
  const startedAt = Date.now();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: historyToSend })
    });
    const data = await res.json();
    const waited = Date.now() - startedAt;
    if (waited < MIN_TYPING_MS) await new Promise(function (r) { setTimeout(r, MIN_TYPING_MS - waited); });
    if (typingEl) typingEl.remove();
    const wrap = addBubble("", "bot");
    chatLog.push({ who: "bot", text: data.reply, citations: data.citations || [] });
    saveChatState();
    if (wrap) {
      typeBubble(wrap.querySelector(".bubble"), data.reply, function () {
        // Ipinapakita lang ang citation pagkatapos matapos mag-"type" ng
        // sagot, para hindi ito makasagabal habang umaanimate pa ang teksto.
        if (data.citations && data.citations.length) {
          wrap.querySelector(".msg-citations").textContent = data.citations.join(" • ");
        }
      });
    }
  } catch (err) {
    if (typingEl) typingEl.remove();
    const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
    addBubble(lang === "en" ? "There was a connection error with the server." : "May error sa koneksyon sa server.", "bot");
  }
}

// ---------- Chat session persistence ----------
// Sinusunod dito ang parehong pattern na ginagamit na ng laro (tingnan ang
// "SESSION PROGRESS" sa static/booth.js): gamit ang sessionStorage (hindi
// localStorage), manatili ang huling pag-uusap habang lumilipat ka sa
// ibang parte ng site (hal. sa laro) at bumalik sa chat, pero mag-reset
// lang kapag TALAGANG ni-refresh ang mismong pahina. Ginagamit ang
// Navigation Timing API para makilala ang totoong refresh laban sa
// normal na navigation/pagbalik sa pagitan ng mga pahina.
const CHAT_STORAGE_KEY = "cicl_chat_state";
let chatLog = [];

function isChatPageReload() {
  try {
    const nav = performance.getEntriesByType && performance.getEntriesByType("navigation")[0];
    if (nav) return nav.type === "reload";
    if (performance.navigation) return performance.navigation.type === 1;
  } catch (e) { /* ignore */ }
  return false;
}

function saveChatState() {
  if (!chatLog.length) return;
  try { sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(chatLog)); }
  catch (e) { /* sessionStorage unavailable -- ok lang, wala lang saved history */ }
}

function clearChatState() {
  try { sessionStorage.removeItem(CHAT_STORAGE_KEY); } catch (e) { /* ignore */ }
}

function restoreChatState() {
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
    const saved = raw && JSON.parse(raw);
    if (!saved || !Array.isArray(saved) || !saved.length) return false;
    const box = document.getElementById("messages");
    if (!box) return false;
    // Palitan lang ang default/hardcoded na welcome bubble ng template kapag
    // may talagang naka-save na history -- hindi ito ginagalaw kung wala pa
    // (unang bisita, o pagkatapos talagang mag-refresh).
    box.innerHTML = "";
    saved.forEach(function (entry) {
      addBubble(entry.text, entry.who, entry.citations);
    });
    chatLog = saved;
    return true;
  } catch (e) { return false; }
}

if (document.getElementById("messages")) {
  if (isChatPageReload()) {
    clearChatState();
  } else {
    restoreChatState();
  }
}

const sendBtn = document.getElementById("send-btn");
if (sendBtn) sendBtn.addEventListener("click", function () { sendMessage(); });

const inputBox = document.getElementById("user-input");
if (inputBox) inputBox.addEventListener("keydown", function (e) { if (e.key === "Enter") sendMessage(); });

document.querySelectorAll(".quick-q").forEach(function (btn) {
  // Ang backend (Gemini) ay tumutugon sa wika ng MISMONG tanong na
  // ipinadala (detect_lang), kaya kung Ingles ang UI mode, dapat din
  // Ingles ang aktwal na text na ipinapadala -- hindi lang ang naka-label
  // sa button -- kung hindi, mananatiling Tagalog ang sagot kahit
  // naka-English mode na ang user.
  btn.addEventListener("click", function () {
    const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
    const msg = lang === "en"
      ? (btn.getAttribute("data-en") || btn.getAttribute("data-msg") || btn.textContent)
      : (btn.getAttribute("data-msg") || btn.textContent);
    sendMessage(msg);
  });
});

const micBtn = document.getElementById("mic-btn");
if (micBtn) micBtn.addEventListener("click", function () {
  const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
  const msg = lang === "en"
    ? "Speech input is still in progress. Please use text for now."
    : "Ginagawa pa ang speech feature. Gamitin muna ang text sa ngayon.";
  addBubble(msg, "bot");
});

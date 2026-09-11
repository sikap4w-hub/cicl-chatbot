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

// ---------- Isang-request-lang-sa-isang-pagkakataon guard ----------
// Bago ito, posibleng makapag-double-send ang user (double click sa Send,
// o pindutin ang Enter habang hinihintay pa ang naunang sagot), na
// nagdudulot ng magkakapatong na request at posibleng magkahalo-halong
// pagkakasunod-sunod ng mga bubble/chatLog entries. Dito, isang GLOBAL flag
// (requestInFlight) ang bantay: habang totoo ito, naka-disable ang input,
// ang Send button, at lahat ng quick-question na buton -- kaya walang
// bagong CHAT request ang maipapadala hangga't hindi pa tapos (o na-cancel
// dahil sa error) ang kasalukuyang isa. Ang mic button ay HIWALAY na
// kino-kontrol (tingnan ang setMicEnabled) dahil kailangan itong manatiling
// pwedeng i-click sa RECORDING state (para itigil ang recording) kahit
// naka-disable na ang ibang input.
let requestInFlight = false;

function setInputEnabled(enabled) {
  const input = document.getElementById("user-input");
  const sendBtnEl = document.getElementById("send-btn");
  if (input) input.disabled = !enabled;
  if (sendBtnEl) sendBtnEl.disabled = !enabled;
  document.querySelectorAll(".quick-q").forEach(function (btn) {
    btn.disabled = !enabled;
  });
}

function setMicEnabled(enabled) {
  const micBtnEl = document.getElementById("mic-btn");
  if (micBtnEl) micBtnEl.disabled = !enabled;
}

async function sendMessage(text) {
  if (requestInFlight) return; // may kasalukuyan nang request -- huwag payagan ang panibago
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

  requestInFlight = true;
  setInputEnabled(false);
  setMicEnabled(false);

  addBubble(msg, "user");
  chatLog.push({ who: "user", text: msg });
  saveChatState();
  // Kung galing sa isang STT recording ang sinusundan nitong mensahe (at
  // pinagana ang Pilot Mode -- tingnan sa ibaba), ito na ang FINAL na
  // tekstong aktwal na ipinadala ng user, kaya dito i-pair ang audio sa
  // tamang "ground truth" label bago i-clear ang reference dito.
  maybeSavePilotPair(msg);
  input.value = "";
  const typingEl = showTyping();
  const startedAt = Date.now();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: historyToSend })
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
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
        // Muling paganahin ang input/buttons pagkatapos lamang matapos
        // mag-"type" ang buong sagot -- hindi bago pa nito matapos i-render,
        // para hindi maabutan ng bagong request ang typeBubble na
        // nag-a-animate pa.
        requestInFlight = false;
        setInputEnabled(true);
        setMicEnabled(true);
        if (input) input.focus();
      });
    } else {
      requestInFlight = false;
      setInputEnabled(true);
      setMicEnabled(true);
    }
  } catch (err) {
    if (typingEl) typingEl.remove();
    const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
    addBubble(lang === "en" ? "There was a connection error with the server." : "May error sa koneksyon sa server.", "bot");
    requestInFlight = false;
    setInputEnabled(true);
    setMicEnabled(true);
    if (input) input.focus();
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
    // Bantay laban sa sira/hindi-inaasahang laman ng sessionStorage (hal.
    // dating manu-manong binago sa DevTools, o entry na walang "text"/"who")
    // -- sinasala lang ang mga entry na may tamang hugis, sa halip na
    // basta ipasa ang lahat sa addBubble (na maaaring mag-crash kapag
    // undefined ang text/who).
    const clean = saved.filter(function (entry) {
      return entry && typeof entry.text === "string" &&
        (entry.who === "user" || entry.who === "bot");
    });
    if (!clean.length) { clearChatState(); return false; }
    box.innerHTML = "";
    clean.forEach(function (entry) {
      addBubble(entry.text, entry.who, entry.citations);
    });
    chatLog = clean;
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
if (inputBox) inputBox.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !requestInFlight) sendMessage();
});

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

// ---------- SOP1 (live mode): salita-kada-salitang speech-to-text ----------
// Dati, ang mic button ay batay sa Whisper pipeline (stt_engine.py, via
// /api/stt): mag-re-record, ipapadala ang BUONG audio, tapos maghihintay
// ng isang buong transcription pagkatapos matapos magsalita. Sinadyang
// PINALITAN ito dito ng browser's sariling Web Speech API
// (SpeechRecognition), para makamit ang TUNAY na live, salita-kada-
// salitang pagpapakita ng teksto HABANG nagsasalita -- hindi na kailangan
// pang maghintay ng round-trip papunta sa server.
//
// Desisyon ito ng thesis team: ang na-depensahan sa study ay ang
// TITULO/paksa nito (Taglish STT support system para sa CICL), hindi
// partikular na nakatali sa Whisper bilang TANGING paraan ng pag-capture
// ng boses sa live chat UI -- flexible ang aktwal na engine dito.
//
// MAHALAGANG PAGKAKAIBA: ang Web Speech API ay CLOUD-BASED (kailangan ng
// internet, gumagamit ng sariling speech recognition service ng browser
// mismo -- HINDI ang naka-fine-tune na Whisper model ng proyektong ito),
// at pinakamaganda ang suporta nito sa Chrome/Chromium-based na browser
// (Edge, atbp.) -- limitado o wala ito sa Firefox/Safari. Sa mga
// Chromium-based browser na may built-in privacy blocking (hal. Brave),
// posibleng harangan ang cloud speech service na ito bilang default --
// tingnan ang onerror handler sa ibaba para sa paliwanag kapag nangyari
// ito.
//
// Ang Whisper pipeline mismo (stt_engine.py, /api/stt) ay HINDI inalis sa
// codebase -- nandiyan pa rin ito para sa offline WER measurement
// (baseline_wer.py) -- pero hindi na ito ang ginagamit ng live mic button.
let speechRecognition = null;
let recognitionFinalText = "";
let isRecording = false;
let lastRecordingBlob = null; // audio ng pinakahuling recording, kung meron (tingnan ang Pilot Mode sa ibaba)
let recordingTimeout = null;
const MAX_RECORDING_MS = 15000; // safety cap kung sakaling hindi mag-fire ang onspeechend/onend

// Bukod sa live transcription (na hawak ng SpeechRecognition sa itaas),
// kailangan pa rin ng ISA PANG PARALLEL na MediaRecorder kung ON ang
// Pilot Mode -- dahil ang Web Speech API mismo ay HINDI nagbibigay ng
// access sa raw audio na nire-record nito, samantalang kailangan ng Pilot
// Mode ang aktwal na audio file (hindi lang ang teksto) para i-save
// bilang bagong training pair para sa SOP1 fine-tuning sa hinaharap.
// Tumatakbo ito nang tahimik sa background, walang epekto sa live
// transcription mismo.
let pilotAudioRecorder = null;
let pilotAudioChunks = [];
let pilotAudioStream = null;

function speechRecognitionSupported() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function speechLangCode() {
  const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
  return lang === "en" ? "en-PH" : "fil-PH";
}

function setMicRecordingUI(recording) {
  const micBtnEl = document.getElementById("mic-btn");
  if (!micBtnEl) return;
  micBtnEl.classList.toggle("recording", recording);
  const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
  micBtnEl.title = recording
    ? (lang === "en" ? "Listening... tap to stop" : "Nakikinig... i-tap para itigil")
    : (lang === "en" ? "Speech input" : "Speech input");
}

async function startRecording() {
  if (requestInFlight) return; // may kasalukuyan nang chat request o speech input
  lastRecordingBlob = null;
  if (!speechRecognitionSupported()) {
    const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
    addBubble(lang === "en"
      ? "Speech input isn't supported on this browser. Please use Chrome or a Chromium-based browser, or use text."
      : "Hindi suportado ng browser na ito ang speech input. Gumamit ng Chrome o Chromium-based na browser, o gamitin muna ang text.", "bot");
    return;
  }

  const input = document.getElementById("user-input");
  if (input) input.value = ""; // sinisimulan mula sa wala tuwing magsisimula ng bagong recording
  recognitionFinalText = "";

  const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
  speechRecognition = new SpeechRecognitionCtor();
  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;
  speechRecognition.lang = speechLangCode();

  speechRecognition.onresult = function (event) {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        recognitionFinalText += transcript + " ";
      } else {
        interim += transcript;
      }
    }
    if (input) input.value = (recognitionFinalText + interim).trim();
  };

  speechRecognition.onspeechend = function () {
    // Ginagamit dito ang SARILING built-in na voice-activity-detection ng
    // browser -- awtomatikong tumigil sa sandaling ma-detect nitong
    // tumahimik na ang user, hindi na kailangan ng custom silence-
    // detection code.
    stopRecording();
  };

  speechRecognition.onerror = function (event) {
    const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      addBubble(lang === "en"
        ? "Couldn't access the microphone. Please check your browser permissions, or use text."
        : "Hindi ma-access ang mikropono. Tingnan ang permission ng browser, o gamitin muna ang text.", "bot");
    } else if (event.error === "network") {
      // Sa ilang Chromium-based browser na may built-in privacy blocking
      // (hal. Brave), posibleng harangan bilang default ang cloud speech
      // service na ito -- ito ang pinakakaraniwang sanhi ng "network"
      // error dito, hindi aktwal na walang internet.
      addBubble(lang === "en"
        ? "Speech input couldn't reach its recognition service. If you're using Brave or a similar privacy browser, check its shields/settings for blocked Google services, or use text."
        : "Hindi maabot ng speech input ang recognition service nito. Kung Brave o katulad na privacy browser ang ginagamit, tingnan ang shields/settings nito kung baka naka-block ang Google services, o gamitin muna ang text.", "bot");
    } else if (event.error !== "no-speech" && event.error !== "aborted") {
      addBubble(lang === "en" ? "There was a problem with speech input." : "May problema sa speech input.", "bot");
    }
  };

  speechRecognition.onend = function () {
    finishRecording();
  };

  try {
    speechRecognition.start();
  } catch (e) {
    speechRecognition = null;
    return;
  }

  isRecording = true;
  requestInFlight = true;
  setInputEnabled(false);
  setMicEnabled(true); // pero manatiling pwedeng i-click ulit para itigil
  setMicRecordingUI(true);
  recordingTimeout = setTimeout(function () {
    if (isRecording) stopRecording();
  }, MAX_RECORDING_MS);

  // Tumakbo lang ang parallel audio-capture kung ON ang Pilot Mode
  // (tingnan ang paliwanag sa itaas) -- hindi kritikal kung mabigo ito,
  // magpapatuloy pa rin ang live transcription nang normal.
  if (pilotModeEnabled) {
    try {
      pilotAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      pilotAudioChunks = [];
      pilotAudioRecorder = new MediaRecorder(pilotAudioStream);
      pilotAudioRecorder.ondataavailable = function (e) {
        if (e.data && e.data.size > 0) pilotAudioChunks.push(e.data);
      };
      pilotAudioRecorder.start();
    } catch (e) {
      pilotAudioRecorder = null;
    }
  }
}

function stopRecording() {
  if (speechRecognition && isRecording) {
    isRecording = false;
    setMicRecordingUI(false);
    setMicEnabled(false); // habang tinatapos pa, huwag munang payagang magsimula ulit
    try { speechRecognition.stop(); } catch (e) { /* ignore */ }
  }
  if (pilotAudioRecorder && pilotAudioRecorder.state !== "inactive") {
    try { pilotAudioRecorder.stop(); } catch (e) { /* ignore */ }
  }
}

function finishRecording() {
  clearTimeout(recordingTimeout);
  if (pilotAudioStream) {
    pilotAudioStream.getTracks().forEach(function (t) { t.stop(); });
    pilotAudioStream = null;
  }
  if (pilotAudioChunks.length) {
    lastRecordingBlob = new Blob(pilotAudioChunks, {
      type: (pilotAudioRecorder && pilotAudioRecorder.mimeType) || "audio/webm",
    });
  }
  pilotAudioRecorder = null;
  pilotAudioChunks = [];
  speechRecognition = null;
  isRecording = false;
  setMicRecordingUI(false);
  requestInFlight = false;
  setInputEnabled(true);
  setMicEnabled(true);
  const input = document.getElementById("user-input");
  if (input) input.focus();
}

const micBtn = document.getElementById("mic-btn");
if (micBtn) micBtn.addEventListener("click", function () {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// ---------- Opsyonal na "Pilot Mode" (opt-in STT training data) ----------
// Tingnan ang pilot_data.py para sa buong paliwanag ng disenyo. Buod:
// naka-OFF ito bilang default. Kapag pinindot ang toggle, kailangan
// munang mag-agree sa isang consent screen (kumpirmasyon na 18+ ang
// gumagamit at PROXY SPEAKER lang, hindi aktwal na batang CICL) bago
// mag-activate. Kapag ON, bawat audio na nire-record gamit ang mic
// button dito, kasama ang FINAL na tekstong aktwal na ipinadala
// (pagkatapos i-edit/kumpirmahin ng user), ay ipinapadala sa
// /api/pilot/save para ma-save bilang bagong training pair.
//
// Walang persistent account/login sa buong app na ito (anonymous,
// session-based lang), kaya ang "pagpayag" ay HINDI naka-imbak nang
// permanente -- naka-scope lang ito sa KASALUKUYANG browser session
// (sessionStorage, parehong pattern gaya ng chatLog), at ka-required
// ulit mag-consent kapag TALAGANG na-refresh ang pahina (tingnan ang
// isChatPageReload sa itaas).
const PILOT_STORAGE_KEY = "cicl_pilot_session";
let pilotSessionId = null;
let pilotModeEnabled = false;

function loadPilotState() {
  try {
    const raw = sessionStorage.getItem(PILOT_STORAGE_KEY);
    const saved = raw && JSON.parse(raw);
    if (saved && typeof saved.sessionId === "string" && saved.enabled) {
      pilotSessionId = saved.sessionId;
      pilotModeEnabled = true;
    }
  } catch (e) { /* ignore */ }
}

function savePilotState() {
  try {
    sessionStorage.setItem(PILOT_STORAGE_KEY, JSON.stringify({
      sessionId: pilotSessionId, enabled: pilotModeEnabled,
    }));
  } catch (e) { /* ignore */ }
}

function makeSessionId() {
  try {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
  } catch (e) { /* ignore */ }
  // Fallback para sa mas lumang browser -- random lang, hindi PII, sapat
  // na para makilala ang isang session sa mga log.
  return "pilot-" + Date.now() + "-" + Math.random().toString(36).slice(2);
}

function updatePilotToggleUI() {
  const toggle = document.getElementById("pilot-toggle");
  if (!toggle) return;
  toggle.classList.toggle("on", pilotModeEnabled);
  const lang = (window.ciclLang && window.ciclLang.get()) || "tl";
  const onText = "🔬 Pilot Mode: ON";
  const offText = "🔬 Pilot Mode";
  toggle.textContent = pilotModeEnabled ? onText : offText;
}

// Ang tekstong ITO na kailangang i-pair sa audio ay ang FINAL na
// bersyon na aktwal na ipinadala ng user (galing sa sendMessage) --
// HINDI ang unang STT guess -- kaya ito na ang tunay na "corrected"
// ground-truth label. Tahasang tinitignan din ang requirement na may
// pinagana nang Pilot Mode AT may available na audio bago ito ipadala.
async function maybeSavePilotPair(finalText) {
  if (!pilotModeEnabled || !pilotSessionId || !lastRecordingBlob) return;
  const blob = lastRecordingBlob;
  lastRecordingBlob = null; // gamit lang minsan bawat recording
  try {
    const form = new FormData();
    form.append("audio", blob, "recording.webm");
    form.append("text", finalText);
    form.append("session_id", pilotSessionId);
    form.append("consented", "true");
    // Sinadyang HINDI hinihintay/binabantayan ang resulta nito -- hindi
    // ito dapat makaabala o magpabagal sa normal na chat flow ng user;
    // "best effort" lang ang pag-save ng training data.
    await fetch("/api/pilot/save", { method: "POST", body: form });
  } catch (e) { /* best-effort lang -- ok lang kung minsan mabigo */ }
}

function showPilotConsentModal() {
  const modal = document.getElementById("pilot-consent-modal");
  const check = document.getElementById("pilot-consent-check");
  const accept = document.getElementById("pilot-consent-accept");
  if (!modal) return;
  if (check) check.checked = false;
  if (accept) accept.disabled = true;
  modal.hidden = false;
}

function hidePilotConsentModal() {
  const modal = document.getElementById("pilot-consent-modal");
  if (modal) modal.hidden = true;
}

const pilotToggle = document.getElementById("pilot-toggle");
if (pilotToggle) {
  loadPilotState();
  updatePilotToggleUI();
  pilotToggle.addEventListener("click", function () {
    if (pilotModeEnabled) {
      // Hindi na kailangan ng consent screen para i-OFF -- boluntaryo
      // ito anumang oras, kaya dapat madali itong itigil.
      pilotModeEnabled = false;
      pilotSessionId = null;
      lastRecordingBlob = null;
      savePilotState();
      updatePilotToggleUI();
    } else {
      showPilotConsentModal();
    }
  });
}

const pilotCheck = document.getElementById("pilot-consent-check");
const pilotAccept = document.getElementById("pilot-consent-accept");
const pilotDecline = document.getElementById("pilot-consent-decline");
if (pilotCheck && pilotAccept) {
  pilotCheck.addEventListener("change", function () {
    pilotAccept.disabled = !pilotCheck.checked;
  });
}
if (pilotAccept) {
  pilotAccept.addEventListener("click", async function () {
    if (pilotAccept.disabled) return;
    pilotSessionId = makeSessionId();
    try {
      const form = new FormData();
      form.append("session_id", pilotSessionId);
      await fetch("/api/pilot/consent", { method: "POST", body: form });
    } catch (e) { /* best-effort lang ang consent log; ipagpatuloy pa rin */ }
    pilotModeEnabled = true;
    savePilotState();
    updatePilotToggleUI();
    hidePilotConsentModal();
  });
}
if (pilotDecline) {
  pilotDecline.addEventListener("click", function () {
    hidePilotConsentModal();
  });
}
document.addEventListener("cicl:langchange", updatePilotToggleUI);

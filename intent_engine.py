"""
intent_engine.py - NLP intent recognition, ngayon gamit ang scikit-learn
(dating hand-rolled TF-IDF/cosine, walang external library).

Paano gumagana ngayon:
1. Bawat intent (galing sa game_data/intents.json) ay may listahan ng
   "examples" (Tagalog/Taglish) at "examples_en" (English) - halimbawang
   pangungusap na kumakatawan dito, kahit anong wika ang gamit.
2. Ang lahat ng examples (parehong wika, maliban sa "fallback" na walang
   sariling examples) ay isinasanay bilang labeled na training data sa isang
   scikit-learn Pipeline: TfidfVectorizer (gamit ang SARILING tokenize() sa
   ibaba, kasama ang elongation-collapse at stopword-filtering nito) na
   sinusundan ng LogisticRegression. Awtomatiko pa ring tutugma ang English
   na tanong sa English na examples, at ang Tagalog/Taglish na tanong sa
   Tagalog examples, dahil parehong TF-IDF/word-overlap pa rin ang batayan.
3. Ang intent na may pinakamataas na predict_proba() sa mensahe ng user ang
   siyang tinuturing na "nais sabihin" niya. Kapag masyadong mababa ang
   confidence (below CONFIDENCE_THRESHOLD), "fallback" ang ibabalik.
4. Bukod dito, tinitingnan din ng detect_lang() kung anong wika ang gamit sa
   tanong (Tagalog/Taglish o English) para malaman kung aling bersyon ng
   sagot (responses vs responses_en) ang ibabalik -- Tagalog/Taglish ang
   input, Tagalog ang sagot; English ang input, English ang sagot.

BAKIT NILIPAT SA SCIKIT-LEARN: ang dating hand-rolled cosine-similarity na
bersyon ay sinadyang walang external ML library, pero ito rin ang dahilan
kung bakit hindi ito literal na masasabing "enhanced NLP" -- tugma lang ito
sa pinaka-magkatulad na TRAINING EXAMPLE, hindi tunay na sinanay/"trained"
na modelo. Ang bersyong ito ay gumagamit na ng tunay na supervised learning
(TfidfVectorizer + LogisticRegression, parehong may .fit() sa training data),
kaya't tugma na sa layunin ng SOP 2 (Enhanced NLP Intent Recognition) --
pero PAALALA: hangga't wala pang totoong Taglish speech-derived na
intent-annotated dataset (SOP 1 pa lang ang kailangan dito, hindi pa
built), ang tanging "training data" na mayroon ay ang parehong maliit na
listahan ng examples sa intents.json na ginamit na rin ng dating bersyon --
kaya ang tunay na benepisyo ngayon ay sa PAMAMARAAN (real ML pipeline,
madaling palitan/i-retrain kapag may bagong data na), hindi pa sa laki ng
data.

Ang tokenize()/_collapse_trailing_elongation()/detect_lang() sa ibaba ay
HINDI ginalaw -- pareho pa ring ginagamit ng TfidfVectorizer sa itaas bilang
custom tokenizer, kaya nananatili ang mga natutunang ayos dito (trailing-only
elongation collapse, stopword filtering) nang walang pagbabago.
"""
import json
import random
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE = Path(__file__).parent
INTENTS_PATH = BASE / "game_data" / "intents.json"

# Ibang saklaw ng confidence values ang LogisticRegression predict_proba()
# kumpara sa dating cosine similarity, kaya ibang threshold din ang tama --
# na-verify ito sa pamamagitan ng regression testing laban sa parehong
# established test set na ginamit noong cosine pa ang ginagamit (mga
# maikling greeting/thanks kahit may elongation, hanggang sa mga compound na
# mensaheng may tunay na tanong sa loob -- tingnan ang docstring ng
# _try_conversational_shortcut() sa gemini_engine.py para sa buong listahan).
CONFIDENCE_THRESHOLD = 0.30

# Karaniwang salitang Tagalog/Taglish/English na hindi gaanong nagdadala ng
# kahulugan para sa pagkilala ng intent (function words). Tinatanggal
# ito bago kunin ang mga content word.
STOPWORDS = {
    "ang", "ng", "sa", "mga", "ko", "mo", "niya", "namin", "natin", "nila",
    "ako", "ikaw", "siya", "kami", "tayo", "kayo", "sila", "po", "opo",
    "ba", "na", "pa", "din", "rin", "naman", "lang", "lamang", "yung",
    "yun", "ito", "iyon", "at", "o", "kung", "kasi", "dahil", "para",
    "kapag", "pero", "may", "meron", "wala", "ay", "hindi", "sana",
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on",
    "and", "i", "you", "he", "she", "we", "they", "my", "your", "his",
    "her", "our", "their", "this", "that", "these", "those", "who", "how",
    "why", "when", "where", "which", "do", "does", "did", "can", "could",
    "will", "would", "should", "have", "has", "had", "not", "no", "for",
    "with", "about", "if", "because", "just", "so", "but", "up", "still",
    "there", "here", "be", "am", "it", "its",
}

TOKEN_RE = re.compile(r"[a-zA-Z0-9ñÑ]+(?:-[a-zA-Z0-9]+)?")

# NATUKLASANG BUG (adversarial testing): mga casual/excited na pagbabaybay
# ng tunay na greeting/thanks (hal. "Hiiiii", "heyy", "salamuchhh") ay
# nagbibigay ng 0.0 confidence -- ZERO overlap sa training examples --
# dahil sa paulit-ulit na letra na walang katumbas na eksaktong salita sa
# intents.json. Resulta: nahuhulog ang mga simpleng bating ito sa
# NO_CONTEXT_FALLBACK/CLARIFICATION_FALLBACK na parang seryosong tanong
# ito na walang nahanap na sagot -- malamig at hindi angkop para sa isang
# batang nagpapakita lang ng excitement o pasasalamat.
#
# UNANG TANGKANG AYOS (NAKAPIT/NASIRA, sinalo bago pa na-ship): i-collapse
# ang ANUMANG run ng 3+ magkasunod na parehong letra kahit SAAN sa salita.
# NAKAKA-CORRUPT PALA ITO ng mga TUNAY na salita -- "maaari" (isang
# napakakaraniwang Tagalog na salita) ay may GENUINE na 3 magkasunod na
# "a" sa GITNA nito, kaya na-collapse ito papuntang "mari" (maling salita).
#
# TAMANG AYOS: i-collapse lang ang run kapag nasa DULO ng token ito (hindi
# saan mang bahagi), dahil ang elongation-for-emphasis ay palaging
# nangyayari sa HULING tunog ng salita ("hiiiii", "salamuchhh", "pooo"),
# hindi sa gitna -- samantalang ang mga tunay na salita na may paulit-ulit
# na letra (tulad ng "maaari") ay laging nasa GITNA ito, hindi sa dulo.
# Ligtas din ito para sa mga salitang English na nagtatapos sa DALAWANG
# magkaparehong letra (hal. "still", "miss") dahil 3+ (hindi 2) ang
# kailangan bago mag-trigger ang collapse.
#
# ROUND-3 NA NATUKLASANG BUG (partner's testing): "Heeeyyy" ay may DALAWANG
# HIWALAY na elongated run sa dulo ("eee" tapos "yyy"), pero ang regex sa
# itaas ay isang beses lang tumatakbo at ang "$" ay tumutugma lang sa PINAKA
# HULING run -- kaya "yyy" lang ang na-collapse, natitira pa ring "heeey"
# (hindi "hey") na wala pa ring tugma sa training vocab. AYOS: sa halip na
# isang solong run lang, hinahanap muna ang PUNONG "trailing elongation
# zone" -- ang pinakamahabang suffix ng token na binubuo LAMANG ng magkakasunod
# na 3+-repeat runs (maaaring magkaibang letra bawat run, basta bawat isa ay
# sariling 3+ na paulit-ulit na letra, at magkadugtong hanggang sa dulo ng
# token) -- tapos doon lang, sa LOOB ng nahanap na zone na iyon, kino-collapse
# ang BAWAT run nang paisa-isa. Ligtas pa rin ito para sa "maaari" dahil ang
# "aaa" doon ay HINDI nasa dulo (may "ri" pa pagkatapos nito), kaya hindi ito
# kasama sa "trailing zone" kahit paano.
_TRAILING_ELONGATION_ZONE_RE = re.compile(r"(?:(.)\1{2,})+$")
_SINGLE_ELONGATION_RUN_RE = re.compile(r"(.)\1{2,}")


def _collapse_trailing_elongation(token):
    m = _TRAILING_ELONGATION_ZONE_RE.search(token)
    if not m:
        return token
    prefix = token[: m.start()]
    collapsed_zone = _SINGLE_ELONGATION_RUN_RE.sub(r"\1", m.group(0))
    return prefix + collapsed_zone


def tokenize(text):
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
    tokens = [_collapse_trailing_elongation(t) for t in tokens]
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ----------------------------------------------------------------
# Simpleng language detector: Tagalog/Taglish vs English.
# Hindi ito "AI" model -- word-list heuristic lang, pero sapat na para
# malaman kung anong bersyon ng sagot (Tagalog o English) ang ibabalik.
# Kung may kahit isang Tagalog marker sa mensahe (kasama na ang mga
# particle tulad ng "po", "ba", "kasi"), Tagalog/Taglish ito ituturing --
# kaya kahit halo-halong Taglish, Tagalog-flavored pa rin ang sagot.
# ----------------------------------------------------------------
TAGALOG_MARKERS = {
    "ang", "ng", "mga", "ako", "ikaw", "siya", "kami", "tayo", "kayo",
    "sila", "ko", "mo", "niya", "namin", "natin", "nila", "po", "opo",
    "ba", "na", "pa", "din", "rin", "naman", "lang", "lamang", "yung",
    "yun", "ito", "iyon", "kung", "kasi", "dahil", "para", "kapag",
    "pero", "may", "meron", "wala", "hindi", "sana", "paano", "saan",
    "sino", "ano", "bakit", "kailan", "gaano", "gusto", "pwede", "puwede",
    "dapat", "talaga", "doon", "dito", "diyan", "atin", "akin", "iyo",
    "kanya", "huwag", "wag", "yan", "ganito", "ganyan", "ganoon", "tsaka",
    "kayong", "kaming", "nang", "mag", "magsisimula", "managot", "batas",
}
ENGLISH_MARKERS = {
    "what", "who", "how", "why", "when", "where", "which", "do", "does",
    "did", "can", "could", "will", "would", "should", "have", "has",
    "had", "is", "are", "was", "were", "the", "this", "that", "my",
    "your", "you", "help", "me", "right", "rights", "case", "child",
    "law", "for", "with", "about", "because", "yes", "no", "thanks",
    "thank", "please", "much", "very", "hello", "hi", "hey", "i'm",
    "im", "scared", "there", "still", "sorry",
}


def detect_lang(text):
    """Ibinabalik: "tl" (Tagalog/Taglish) o "en" (English)."""
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return "tl"
    tl_hits = sum(1 for t in tokens if t in TAGALOG_MARKERS)
    en_hits = sum(1 for t in tokens if t in ENGLISH_MARKERS)
    if en_hits > 0 and tl_hits == 0:
        return "en"
    return "tl"


class IntentEngine:
    def __init__(self, intents_path=INTENTS_PATH):
        data = json.loads(Path(intents_path).read_text(encoding="utf-8"))
        self.intents = {i["id"]: i for i in data["intents"]}

        # X/y: parehong TRAINING DATA gaya ng dati (Tagalog "examples" +
        # English "examples_en" ng bawat intent, maliban sa "fallback" na
        # walang sariling examples -- hindi ito puwedeng maging isang klase
        # ng supervised classifier na walang example, kaya "fallback" ang
        # ibinabalik sa halip kapag mababa ang confidence ng lahat ng tunay
        # na klase, tulad ng dati).
        X, y = [], []
        for intent in data["intents"]:
            if intent["id"] == "fallback":
                continue
            all_examples = list(intent.get("examples", [])) + list(intent.get("examples_en", []))
            for example in all_examples:
                X.append(example)
                y.append(intent["id"])

        # tokenizer=tokenize (ang parehong function sa itaas, may elongation
        # collapse at stopword filtering na) + preprocessor na walang ginagawa
        # + token_pattern=None ay ang tamang paraan para gamitin ang SARILING
        # tokenizer ng TfidfVectorizer sa halip na ang default nito.
        # ngram_range=(1, 2) para makuha rin ang mga dalawang-salitang parirala
        # (hal. "hindi legal", "record ko"), hindi lang pantay na salita.
        # class_weight="balanced" dahil malaki ang pagkakaiba ng bilang ng
        # examples bawat intent (3 hanggang 19), kaya kung hindi ito
        # gagamitin, mananaig lagi ang mga intent na may pinakamaraming
        # examples (greeting, thanks) kahit hindi talaga sila ang pinaka-tugma.
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                tokenizer=tokenize,
                preprocessor=lambda s: s,
                token_pattern=None,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            )),
            ("clf", LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                C=5.0,
            )),
        ])
        self.pipeline.fit(X, y)

    def classify(self, text):
        """Ibinabalik: (intent_id, confidence)"""
        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        best_idx = proba.argmax()
        best_intent, best_score = classes[best_idx], float(proba[best_idx])
        if best_score < CONFIDENCE_THRESHOLD:
            return "fallback", best_score
        return best_intent, best_score

    def respond(self, text):
        intent_id, confidence = self.classify(text)
        intent = self.intents.get(intent_id, self.intents["fallback"])
        lang = detect_lang(text)
        responses = intent.get("responses_en") if lang == "en" else None
        if not responses:
            lang = "tl"
            responses = intent["responses"]
        reply = random.choice(responses)
        return {"reply": reply, "intent": intent_id, "confidence": round(confidence, 3), "lang": lang}


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = IntentEngine()
    return _engine

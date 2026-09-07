"""
intent_engine.py - Simpleng NLP intent recognition (walang malaking dependency).

Paano gumagana:
1. Bawat intent (galing sa game_data/intents.json) ay may listahan ng
   "examples" (Tagalog/Taglish) at "examples_en" (English) - halimbawang
   pangungusap na kumakatawan dito, kahit anong wika ang gamit.
2. Ginagawang TF-IDF vector ang LAHAT ng examples (parehong wika), at ang
   bagong mensahe ng user. Dahil dito, nakikilala ang intent kahit Tagalog,
   Taglish, o pure English ang tanong -- ang TF-IDF/cosine ay batay sa
   pagtutugma ng salita, kaya awtomatikong tutugma ang English na tanong sa
   English na examples, at ang Tagalog/Taglish na tanong sa Tagalog examples.
3. Ang intent na pinakamalapit (cosine similarity) sa mensahe ng user ang
   siyang tinuturing na "nais sabihin" niya. Kapag masyadong mababa ang
   pagkakatugma (below CONFIDENCE_THRESHOLD), "fallback" ang ibabalik.
4. Bukod dito, tinitingnan din ng detect_lang() kung anong wika ang gamit sa
   tanong (Tagalog/Taglish o English) para malaman kung aling bersyon ng
   sagot (responses vs responses_en) ang ibabalik -- Tagalog/Taglish ang
   input, Tagalog ang sagot; English ang input, English ang sagot.

Sadyang walang external ML library (scikit-learn, transformers, atbp.) para
hindi na kailangan pang mag-install ng malalaking package -- built-in na
Python lang (re, math, random) ang ginamit. Sapat na ito para sa laki ng
intent inventory na ito, at madaling palawakin (magdagdag lang ng mga bagong
"examples"/"examples_en" sa intents.json, hindi na kailangang baguhin ang
code na ito).
"""
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent
INTENTS_PATH = BASE / "game_data" / "intents.json"

CONFIDENCE_THRESHOLD = 0.22

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


def tokenize(text):
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
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

        # docs: listahan ng (intent_id, token_list) para sa bawat example,
        # kasama ang Tagalog ("examples") at English ("examples_en")
        # bersyon -- pareho itong itinuturing na training data ng parehong
        # intent, kaya nakikilala ang parehong wika nang walang extra code.
        self.docs = []
        for intent in data["intents"]:
            all_examples = list(intent.get("examples", [])) + list(intent.get("examples_en", []))
            for example in all_examples:
                toks = tokenize(example)
                if toks:
                    self.docs.append((intent["id"], toks))

        self._build_idf()
        self.doc_vectors = [
            (intent_id, self._vectorize(toks)) for intent_id, toks in self.docs
        ]

    def _build_idf(self):
        n_docs = len(self.docs)
        df = Counter()
        for _, toks in self.docs:
            for term in set(toks):
                df[term] += 1
        # smoothed idf, katulad ng ginagawa ng scikit-learn
        self.idf = {
            term: math.log((1 + n_docs) / (1 + freq)) + 1.0
            for term, freq in df.items()
        }
        self.n_docs = n_docs

    def _vectorize(self, tokens):
        if not tokens:
            return {}
        tf = Counter(tokens)
        vec = {}
        for term, count in tf.items():
            idf = self.idf.get(term)
            if idf is None:
                continue  # salitang hindi nakita sa training examples
            vec[term] = count * idf
        norm = math.sqrt(sum(w * w for w in vec.values()))
        if norm > 0:
            vec = {t: w / norm for t, w in vec.items()}
        return vec

    @staticmethod
    def _cosine(vec_a, vec_b):
        if not vec_a or not vec_b:
            return 0.0
        # umiikot sa mas maikling vector para mas mabilis
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        return sum(w * vec_b.get(t, 0.0) for t, w in vec_a.items())

    def classify(self, text):
        """Ibinabalik: (intent_id, confidence, best_matching_example_tokens)"""
        query_vec = self._vectorize(tokenize(text))
        best_intent, best_score = "fallback", 0.0
        for intent_id, doc_vec in self.doc_vectors:
            score = self._cosine(query_vec, doc_vec)
            if score > best_score:
                best_intent, best_score = intent_id, score
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

"""
law_retrieval.py
-----------------
Simpleng TF-IDF + cosine-similarity retrieval sa ibabaw ng game_data/law_chunks.json
(ginawa ng build_lawbase.py). Parehong diskarte sa intent_engine.py -- walang
external na library, walang training, deterministic -- pero dito, sa halip
na intent ang inihahanap, mga bahagi ng batas (RA 9344 / RA 10630 / Revised
IRR) ang kinukuha na pinaka-related sa tanong ng user, para isama bilang
"grounding context" sa prompt na ipapadala kay Gemini.

Ang retrieval na ito ang dahilan kung bakit hindi basta-basta gumagawa ng
sagot si Gemini mula sa sarili niyang "memorya" ng batas (na maaaring mali o
luma) -- dapat laging galing sa mismong teksto ng batas na nasa
game_data/law_chunks.json.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent
CHUNKS_PATH = BASE / "game_data" / "law_chunks.json"

STOPWORDS = {
    "ang", "ng", "sa", "mga", "na", "ay", "at", "kung", "ba", "po", "ako",
    "ikaw", "siya", "kami", "tayo", "kayo", "sila", "ko", "mo", "niya",
    "namin", "natin", "nila", "pa", "din", "rin", "naman", "lang", "yung",
    "yun", "ito", "iyon", "kasi", "dahil", "para", "kapag", "pero", "may",
    "meron", "wala", "hindi", "sana", "paano", "saan", "sino", "ano",
    "bakit", "kailan", "gaano", "gusto", "pwede", "puwede", "dapat",
    "the", "a", "an", "of", "to", "in", "is", "are", "was", "were", "be",
    "been", "being", "and", "or", "but", "if", "then", "so", "for", "with",
    "as", "by", "on", "at", "from", "that", "this", "it", "what", "who",
    "how", "why", "when", "where", "which", "do", "does", "did", "can",
    "could", "will", "would", "should", "have", "has", "had", "my", "your",
}


def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9ñÑ']+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


# Ang pormal na teksto ng batas ay gumagamit ng legal/Ingles na termino
# ("detention", "imprisonment", "diversion"), samantalang ang mga bata ay
# nagtatanong sa kolokyal/Taglish na paraan ("makukulong", "kulong",
# "ikukulong ba ako"). Purong TF-IDF na exact-token-match lang ay hindi
# makikita ang koneksyon nito, kaya dito idinadagdag ang katumbas na
# pormal na termino bago mag-search, para mahanap pa rin ang tamang batas
# kahit kolokyal ang tanong.
QUERY_SYNONYMS = {
    "makukulong": ["detention", "kulong", "imprisonment", "bahay", "pagasa"],
    "ikukulong": ["detention", "kulong", "imprisonment", "bahay", "pagasa"],
    "kulungan": ["detention", "kulong", "youth", "rehabilitation", "center"],
    "nakulong": ["detention", "kulong", "imprisonment"],
    "makukulong'": ["detention"],
    "parusa": ["penalty", "disposition", "intervention", "diversion"],
    "multa": ["fine", "penalty"],
    "kaso": ["case", "offense", "proceedings"],
    "diskarnment": ["discernment"],
    "sagot": ["responsibility", "liability"],
    "managot": ["liability", "responsibility", "criminal"],
    "edad": ["age", "minimum"],
    "tulong": ["intervention", "assistance", "diversion"],
    "totoo": ["truth", "discernment", "assessment"],
    "barkada": ["peer", "diversion", "intervention"],
    "magulang": ["parent", "custody", "guardian"],
    "abogado": ["counsel", "lawyer", "pao"],
    "karapatan": ["rights"],
    "takot": ["fear", "assistance", "intervention"],
    "natatakot": ["fear", "assistance", "intervention"],
    "makakatulong": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "tumulong": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "matulungan": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "kausapin": ["assistance", "social", "worker", "lswdo", "counsel", "barangay"],

    # Ang mga entry sa itaas ay Tagalog->English lang (dahil Ingles ang
    # aktwal na teksto ng batas). Pero napansin sa live testing na
    # kolokyal/simpleng ENGLISH na tanong (hal. "Who can help me?", "Does
    # it help if I tell the truth?") ay ZERO hits din -- ang salitang
    # "help" mismo ay hindi literal na lumalabas sa legal text (gumagamit
    # ito ng "assistance" sa halip), kaya kailangan din ng English->English
    # synonym coverage, hindi lang Tagalog->English.
    "help": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "helps": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "helping": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "assist": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "support": ["assistance", "intervention", "social", "worker", "lswdo", "counsel", "barangay"],
    "tell": ["truth", "discernment", "assessment", "admission", "diversion"],
    "truth": ["discernment", "assessment", "admission", "diversion"],
    "honest": ["truth", "discernment", "assessment", "admission"],
    "confess": ["admission", "diversion", "discernment"],
    "admit": ["admission", "diversion", "discernment"],
    "silent": ["rights", "counsel", "assistance", "pao"],
    "silence": ["rights", "counsel", "assistance", "pao"],
    "jail": ["detention", "imprisonment", "bahay", "pagasa"],
    "jailed": ["detention", "imprisonment", "bahay", "pagasa"],
    "prison": ["detention", "imprisonment", "bahay", "pagasa"],
    "arrested": ["custody", "apprehension", "detention"],
    "punishment": ["penalty", "disposition", "intervention", "diversion"],
    "punished": ["penalty", "disposition", "intervention", "diversion"],
    "lawyer": ["counsel", "pao"],
    "inaresto": ["custody", "apprehension", "detention"],
    "aresto": ["custody", "apprehension", "detention"],
    "hinuli": ["custody", "apprehension", "detention"],
    "habambuhay": ["life", "imprisonment", "capital", "punishment"],
    "rekord": ["record", "confidentiality", "confidential"],

    # Natuklasan sa "get away with it" adversarial testing na kahit ilang
    # mahalagang salita (kasama na ang PINAKAMATINDING kaso -- pagpatay)
    # ay walang synonym coverage, kaya nabigo ang retrieval kahit real at
    # seryosong tanong ito.
    "krimen": ["case", "offense", "crime"],
    "kasalanan": ["case", "offense", "violation"],
    "mapaparusahan": ["penalty", "disposition", "punishment", "accountability"],
    "paparusahan": ["penalty", "disposition", "punishment", "accountability"],
    "parurusahan": ["penalty", "disposition", "punishment", "accountability"],
    "mangyayari": ["consequence", "disposition", "intervention", "accountability"],
    "lusot": ["accountability", "intervention", "diversion", "disposition"],
    "makakalusot": ["accountability", "intervention", "diversion", "disposition"],
    "makalusot": ["accountability", "intervention", "diversion", "disposition"],
    "pinatay": ["murder", "heinous", "serious", "grave"],
    "pumatay": ["murder", "heinous", "serious", "grave"],
    "papatayin": ["murder", "heinous", "serious", "grave"],
    "pagpatay": ["murder", "heinous", "serious", "grave"],
    "record": ["confidentiality", "confidential", "privileged"],
    "tago": ["confidentiality", "confidential", "privileged"],

    # Karagdagang gaps na natuklasan sa third round ng "get away with it"
    # adversarial testing: "Anong gagawin sa akin?" at "Kung nanakit ako ng
    # tao nang malubha..." ay parehong nabigo sa retrieval (fallback).
    "gagawin": ["disposition", "intervention", "diversion", "procedure", "custody"],
    "nanakit": ["physical", "injury", "serious", "grave", "offense"],
    "saktan": ["physical", "injury", "serious", "grave", "offense"],
    "sinaktan": ["physical", "injury", "serious", "grave", "offense"],
    "nasaktan": ["physical", "injury", "serious", "grave", "offense"],
    "malubha": ["serious", "grave", "heinous", "severe"],

    # "ano connect nito sakin" -- bata na nagtatanong kung paano siya
    # naaapektuhan/sakop ng batas ay gumagamit ng salitang "connect" na
    # walang literal na katumbas sa batas (na gumagamit ng "scope",
    # "cover", "applicability"), kaya nabigo ang retrieval kahit malinaw
    # ang tanong (tungkol ito sa Section 1: Scope ng RA 9344).
    "connect": ["coverage", "scope", "applicability", "minor", "child", "cover"],
    "koneksyon": ["coverage", "scope", "applicability", "minor", "child", "cover"],
    "kinalaman": ["coverage", "scope", "applicability", "minor", "child", "cover"],
    "kaugnayan": ["coverage", "scope", "applicability", "minor", "child", "cover"],

    # Round-2 adversarial testing (partner, Priority 1): zero synonym
    # coverage para sa kolokyal/maling-baybay na Taglish variants ng
    # "detain"/"detention" -- hal. "detine", "dinetine", "ma-detine",
    # "madetine", "na-detine", "pagdetine", "dine-tain", "detined".
    # Hindi lang ito tungkol sa listahan ng eksaktong salitang ito -- ang
    # ugat ng problema ay ang RETRIEVAL ay walang tolerance sa VARYING
    # spelling/conjugation ng konseptong "detention" (kasama na ang mga
    # error na dulot ng speech-to-text sa full system, dahil Taglish STT
    # ay madalas mag-transcribe ng English legal terms nang maling
    # baybay). Idinagdag dito ang lahat ng morphological variant
    # (base, -in/-an affix, ma-/na- stative prefix, pag- nominalization,
    # at hyphenated forms na hinahati ng tokenizer sa magkahiwalay na
    # token dahil walang hyphen support ang tokenize() regex).
    "detine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detain": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "dinetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "madetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "nadetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "pagdetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "magdedetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detained": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detined": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detain'd": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detenido": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detensyon": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "deten": ["detention", "kulong", "bahay", "pagasa", "custody"],
    # "ma-detine", "na-detine", "dine-tain" atbp. ay nahahati ng
    # tokenizer sa magkahiwalay na piraso dahil walang hyphen sa
    # TOKEN_RE nito -- kaya kailangan din ng entry para sa mga piraso
    # mismo (hal. "tain" mula sa "dine-tain").
    "tain": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "detn": ["detention", "kulong", "bahay", "pagasa", "custody"],
    # future/reduplicated Tagalog conjugations ("ma-" + reduplicated
    # first syllable, common sa mga tanong tungkol sa mangyayari pa lang)
    "madedetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "nadedetine": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "dedetenin": ["detention", "kulong", "bahay", "pagasa", "custody"],
    "idedetine": ["detention", "kulong", "bahay", "pagasa", "custody"],

    # Round-4 (item 9): karagdagang kolokyal/maling-baybay na variants na
    # nakita sa pinakahuling test transcript, sinusunod ang parehong
    # ingat na tinuran ng user -- idinagdag lang ang mga ito dahil
    # ipinakita ng aktwal na tanong (hindi basta idinagdag ang bawat
    # posibleng typo na maiisip, dahil maaari itong makasira sa ibang
    # salita nang hindi sinasadya).
    "abugado": ["counsel", "lawyer", "pao"],
    "dibersyon": ["diversion", "intervention"],
    "dibersion": ["diversion", "intervention"],
    "diversyon": ["diversion", "intervention"],
    "kustodiya": ["custody", "detention"],
    "kastodiya": ["custody", "detention"],
    "nahuli": ["custody", "apprehension", "detention"],
    "nahuling": ["custody", "apprehension", "detention"],
    # Sinadyang HINDI idinagdag ang "huli" (walang panlapi) -- masyadong
    # ambiguous ang salitang ito sa Tagalog (maaari ring mangahulugang
    # "late", tulad sa "huling tanong"/"huli na"), kaya maaari itong
    # magdulot ng maling retrieval sa mga tanong na walang kinalaman sa
    # pagkahuli/pag-aresto. Ang mga naka-panlapi lang (nahuli, nahuling,
    # naaresto) ang idinagdag dahil mas malinaw ang kahulugan ng mga ito.
    "naaresto": ["custody", "apprehension", "detention"],
    "maaaresto": ["custody", "apprehension", "detention"],
}


def expand_query(text):
    tokens = tokenize(text)
    extra = []
    for t in tokens:
        extra.extend(QUERY_SYNONYMS.get(t, []))
    return tokens + extra


class LawRetriever:
    def __init__(self, chunks_path=CHUNKS_PATH):
        data = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
        self.chunks = data["chunks"]
        self.docs = []  # (chunk_index, tokens)
        for i, c in enumerate(self.chunks):
            toks = tokenize(c["text"] + " " + c["citation"])
            self.docs.append((i, toks))

        self.df = Counter()
        for _, toks in self.docs:
            for t in set(toks):
                self.df[t] += 1
        self.n_docs = len(self.docs)
        self.doc_vecs = [self._vectorize(toks) for _, toks in self.docs]

    def _idf(self, term):
        df = self.df.get(term, 0)
        return math.log((self.n_docs + 1) / (df + 1)) + 1

    def _vectorize(self, tokens):
        tf = Counter(tokens)
        vec = {t: c * self._idf(t) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    @staticmethod
    def _cosine(v1, v2):
        if len(v2) < len(v1):
            v1, v2 = v2, v1
        return sum(v * v2.get(t, 0.0) for t, v in v1.items())

    def search(self, query, top_k=5, min_score=0.05):
        q_tokens = expand_query(query)
        if not q_tokens:
            return []
        q_vec = self._vectorize(q_tokens)
        scored = []
        for (idx, _), doc_vec in zip(self.docs, self.doc_vecs):
            score = self._cosine(q_vec, doc_vec)
            if score > 0:
                scored.append((score, idx))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scored[:top_k]:
            if score < min_score and results:
                break
            c = self.chunks[idx]
            results.append({"score": round(score, 4), "citation": c["citation"], "text": c["text"], "id": c["id"]})
        return results


_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = LawRetriever()
    return _retriever


if __name__ == "__main__":
    r = get_retriever()
    for q in ["makukulong ba ako", "ano ang diversion", "bahay pag-asa", "minimum age"]:
        print("Q:", q)
        for hit in r.search(q, top_k=3):
            print("  ", hit["score"], hit["citation"])
        print()

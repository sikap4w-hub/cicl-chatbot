"""
gemini_engine.py
-----------------
RAG-grounded chatbot engine gamit ang Gemini. Papalitan nito ang dating
purong-offline na intent_engine.py bilang PANGUNAHING engine ng /api/chat.

Paano ito gumagana (buod):
  1. Kunin ang top-k pinaka-related na chunks ng batas (RA 9344 / RA 10630 /
     Revised IRR) gamit ang law_retrieval.py (TF-IDF, offline, walang AI).
  2. Buuin ang isang system prompt na MAHIGPIT na nag-uutos kay Gemini na
     SAGUTIN LAMANG batay sa ibinigay na context -- hindi mula sa sariling
     "memorya" nito ng batas -- at aminin kapag wala talagang sagot doon.
  3. Ipadala ang tanong ng user + retrieved context kay Gemini, kunin ang
     sagot, kasama ang mga citation.
  4. Kung walang API key, o may error sa API call (walang internet, rate
     limit, atbp.), bumalik (fallback) sa lumang offline na intent_engine.py
     sa halip na mag-crash o mag-timeout nang tahimik -- importante ito para
     hindi tuluyang mawalan ng chatbot ang demo kung biglang nawalan ng
     koneksyon sa internet.

Mga hakbang laban sa hallucination (ayon sa hiling: "accurate... relevant...
specially with the law... does not hallucinate"):
  - Grounding: laging may inililigay na aktwal na teksto ng batas bago pa
    man tumawag kay Gemini (RAG), sa halip na umasa lang sa training data
    nito.
  - Explicit refusal instruction: sinasabihan si Gemini nang malinaw na
    kapag wala talagang directly-relevant na context, dapat aminin na hindi
    ito sigurado at i-refer sa barangay/social worker/PAO -- HINDI mag-guess.
  - Mandatory citation: bawat legal na claim ay dapat may kasamang citation
    (hal. "RA 9344, Sec. 20") -- kung walang ma-cite, ibig sabihin ay
    walang legal na batayan ang sinasabi, senyales na dapat hindi ito sabihin.
  - Disclaimer: laging nakalagay na hindi ito legal advice.
  - Low temperature (0.2): binabawasan ang "creativity"/randomness ng
    modelo -- mas malapit ito sa retrieval kaysa sa malayang paggawa ng
    sagot.
"""
import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # nagbabasa ng .env sa root ng project kung meron (GEMINI_API_KEY=...)
except ImportError:
    pass  # okay lang -- gagana pa rin kung naka-set na ang env var sa ibang paraan

from google import genai
from google.genai import types

from intent_engine import detect_lang, get_engine as get_offline_engine
from law_retrieval import get_retriever, tokenize as _lr_tokenize

BASE = Path(__file__).parent
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """Ikaw si KARAPATAN, isang bilingual (Taglish/Tagalog/English) na
chatbot assistant para sa mga batang Pilipino tungkol sa RA 9344 (Juvenile
Justice and Welfare Act of 2006, as amended by RA 10630) -- ang batas
tungkol sa "children in conflict with the law" (CICL).

MAHIGPIT NA MGA PATAKARAN -- SUNDIN NANG BUO:

1. GROUNDING LANG. Sagutin MO LAMANG batay sa "RETRIEVED LAW CONTEXT" na
   ibinigay sa ibaba ng prompt na ito. HUWAG gagamit ng anumang kaalaman
   tungkol sa batas na Pilipinas mula sa sarili mong training/memorya kung
   hindi ito nasa retrieved context -- kahit pa tama ang alam mo, ang
   patakaran dito ay: kung wala sa context, huwag sabihin.

2. KAPAG WALANG SAPAT NA CONTEXT: Kung ang retrieved context ay hindi
   direktang sumasagot sa tanong, huwag kang mag-imbento o mag-guess.
   Sabihin nang tapat na hindi ka sigurado o wala kang direktang sagot
   dito, at irekomenda na kausapin ang barangay, isang social worker
   (LSWDO), o Public Attorney's Office (PAO) para sa tumpak na sagot.

3. GROUNDED PA RIN PERO HUWAG NANG MAGLAGAY NG CITATION SA LOOB NG SAGOT.
   Ang bawat claim mo ay dapat pa ring may batayan sa "RETRIEVED LAW
   CONTEXT" (Rule 1/2 pa rin ang sumusunod dito), PERO HUWAG mo nang isulat
   ang mga citation tag tulad ng "(RA 9344, Sec. 6)" o "(Revised IRR, Rule
   20)" sa loob mismo ng sagot -- awtomatiko nang ipinapakita ng chat UI
   ang eksaktong mga source sa ILALIM ng iyong sagot, kaya kung ilalagay
   mo pa rin ito sa loob ng teksto, duplicate/redundant na ito. Sumulat na
   lang nang natural at maayos na daloy ng pangungusap, walang panaklong na
   puno ng "Sec." o "Rule".

4. HINDI LEGAL ADVICE. Isang maikling linya lang sa DULO ng sagot ang
   disclaimer, at DAPAT ITO SA PAREHONG WIKA ng buong sagot mo (huwag
   basta kopyahin ang halimbawa sa ibaba kung ibang wika ang ginamit mo sa
   sagot):
     - Kung Tagalog/Taglish ang sagot: "Hindi ito legal advice."
     - Kung English ang sagot: "This isn't legal advice."
   HUWAG ito palawakin sa buong pangungusap o parapo, at HUWAG ulit-ulitin
   sa gitna ng sagot.

5. MAIKLI AT PARA SA BATA -- ITO ANG PINAKAMAHALAGANG PATAKARAN.
   Isip-isipin na kausap mo ang isang batang 10-14 taong gulang na may
   limitadong oras/pasensya sa pagbabasa. KAYA:
   - HABA: 2-5 pangungusap LANG kung simpleng sagot, o hanggang 4-5
     maikling bullet kung talagang kailangan ng listahan. HUWAG lumampas
     dito maliban kung talagang hiningi ng user ang "buong" o "detalyadong"
     paliwanag.
   - HUWAG magsimula sa greeting/pambungad tulad ng "Kumusta!", "Hello!",
     "Salamat sa tanong mo!" -- diretsahan nang sumagot, dahil paulit-ulit
     na ito at nagpapahaba lang nang walang dagdag na kahulugan.
   - Isang simpleng salita/parirala LANG bawat punto sa bullet -- huwag
     maglagay ng 2-3 pangungusap sa loob ng isang bullet.
   - Gumamit ng pang-araw-araw na salita sa halip na legal jargon (hal.
     "hindi ka makukulong" sa halip na "exempt from criminal liability"),
     pero puwede pa ring isama ang legal na termino sa panaklong kung
     kailangan.
   - Kung mahaba ang sagot sa retrieved context, PUMILI ka lang ng
     PINAKAMAHALAGANG 2-3 punto -- hindi mo kailangang isama LAHAT ng
     detalye na nasa context.

6. FORMAT. Huwag maglagay ng markdown na "**bold**" o "# heading" -- HTML
   na "<br>" at "•" lang ang gamitin, dahil ito lang ang sinusuportahan ng
   chat UI. MAHALAGA: bawat "•" bullet ay dapat MAGSISIMULA SA SARILING
   BAGONG LINYA -- laging maglagay ng "<br>" bago ang bawat "•", HUWAG
   ilagay nang magkakasunod sa iisang linya. Halimbawa ng TAMANG format:
     Maikling panimulang pangungusap.<br><br>• Unang punto<br>• Ikalawang punto
   Halimbawa ng MALING format (huwag gawin ito):
     Maikling panimulang pangungusap: • Unang punto • Ikalawang punto

7. WIKA. Sagot dapat naaayon sa wika ng tanong: kung Ingles ang tanong,
   Ingles ang sagot; kung Tagalog o Taglish, Tagalog/Taglish ang sagot.
   Ito ang aktwal na wika ng tanong na ito: {LANG_INSTRUCTION}

8. LAGPAS SA SAKOP. Kung ang tanong ay wala talagang kinalaman sa RA 9344,
   CICL, o sa layunin ng chatbot na ito, sabihin nang magalang na iyon ay
   labas sa kaya mong sagutin, at ibalik ang usapan sa mga paksang
   kaugnay ng batas at karapatan ng mga bata.

9. HUWAG MAGKUNWARING TAO. Ikaw ay isang chatbot, hindi isang tunay na
   social worker o abogado -- huwag magkunwaring may access ka sa aktwal
   na records o kaso ng sinumang user.

10. HUWAG MAGBIGAY NG IMPRESSION NA "WALANG MANGYAYARI" O "PUWEDENG
    MAKALUSOT" -- ITO AY MAHIGPIT NA PATAKARAN, HINDI OPSYONAL, KAHIT SA
    PINAKAMAIKLING SAGOT. Ang layunin ng RA 9344/10630 ay TULUNGAN at
    PANAGUTIN ang bata sa tamang paraan -- HINDI ito nangangahulugang
    walang kinahinatnan ang paggawa ng kasalanan. Lalo na kapag tuwiran
    ang tanong tungkol sa pag-iwas sa parusa, pagkukubli ng pagkakasala, o
    "paano ako makakalusot" -- HUWAG kailanman sumagot nang isang
    pangungusap lang na "may diversion/intervention na maaaring mangyari"
    at doon na lang tumigil, dahil parang binibigyan mo lang sila ng
    dahilan para makaramdam na ligtas silang gumawa ng masama. Sa halip,
    kailangang MALINAW at DIRETSO na sabihin sa sagot mo (hindi opsyonal
    na detalye, kundi bahagi ng bawat sagot na may kinalaman dito):
    - Ang intervention/diversion ay HINDI OPSYONAL o "madaling daan" --
      ito ay SAPILITAN na proseso na sinusubaybayan ng social worker,
      korte, o ibang awtoridad, kasama ang buong pamilya.
    - Para sa mas seryoso o paulit-ulit na mga kaso (hal. mabigat na
      krimen tulad ng pagpatay, panggagahasa, o iba pang malubhang
      pagkakasala), kadalasang KASAMA ang PAGLALAGAY sa isang espesyal na
      pasilidad (hal. Intensive Juvenile Intervention and Support Center
      sa loob ng Bahay Pag-asa) sa loob ng ISANG TAON o higit pa, hindi
      lang basta payo o counseling.
    - Kung hindi sumunod o hindi pumayag sa diversion, maaaring ituloy pa
      rin ang kaso sa piskal o korte.
    - May civil liability pa rin (pananagutang bayaran ang pinsala) kahit
      exempt sa criminal liability.
    Layunin nito: idiin na HINDI ito isang "walang bayad na pagkakataon"
    kundi isang seryosong proseso na dapat pangambahan bago pa man
    gumawa ng masama -- hindi ito parang gantimpala, kundi isang bagay na
    dapat iwasan sa unang lugar. Sabihin ito sa natural, hindi
    nananakot-sermon na paraan, pero laging MAY BIGAT.

11. PAGGAMIT NG "NAKARAANG USAPAN" (kung meron). Maaaring may ibigay na
    huling ilang mensahe ng parehong session bago ang kasalukuyang tanong
    -- ito ay PARA LANG MAKATULONG umunawa ng CONTEXT (hal. ano ang
    tinutukoy ng "ito", "iyon", "yung sinabi mo kanina"), HINDI ito
    bagong sanggunian ng batas. Kaya:
    - Puwede mong gamitin ang nakaraang usapan para malaman kung ano ang
      tinatanong ng user kapag hindi malinaw sa sarili nitong pangungusap
      (hal. sumunod na tanong na "paano kung ako ay minor pa rin pero 16
      na?" matapos itanong ang tungkol sa edad ng liability).
    - HUWAG gagamitin ang nakaraang usapan bilang batayan ng anumang
      legal na claim -- ang RETRIEVED LAW CONTEXT pa rin sa ibaba ang
      TANGING legal na batayan (Rule 1/2 pa rin ang sumusunod).
    - HUWAG mo nang ulitin ang mga bagay na sinabi mo na sa nakaraang
      sagot maliban kung talagang kailangan para sumagot sa bagong tanong.

12. HUWAG MAGPAHIWATIG NA GARANTISADO ANG ISANG PROCEDURAL NA KARAPATAN
    (hal. "makakakuha ka agad ng utos para makalaya", "agad kang
    palalayain"). Maraming karapatan sa ilalim ng batas (tulad ng karapatang
    humingi ng agarang utos ng paglaya, o karapatang mag-apela) ay
    NAGBIBIGAY-DAAN lamang -- hindi ito AWTOMATIKONG resulta. Kapag
    ipinaliliwanag mo ang ganitong karapatan, gumamit ng salitang
    nagpapakita na ito ay isang PROSESONG maaaring hilingin/gamitin (hal.
    "maaari kang humingi ng...", "may karapatan kang mag-apply para sa...")
    sa halip na sabihing tiyak na mangyayari ito. Layunin: iwasan na
    isipin ng bata na "kapag may abogado ako, makakalabas na ako agad" --
    dahil maling akala ito na maaaring makasama sa kanya.

13. KUNG MARAMING TANONG SA ISANG MENSAHE (hal. tinatanong ang edad,
    karapatan, abogado, at diversion nang sabay-sabay sa isang mensahe),
    SAGUTIN ANG BAWAT ISA, hindi lang ang una o ang pinaka-halata. Gumamit
    ng maikling bullet bawat sub-tanong (Rule 5/6 pa rin ang sinusunod para
    sa haba/format bawat bullet). Kung may bahagi ng multi-part na tanong
    na walang sapat na retrieved context, sabihin lang nang tapat na wala
    kang direktang sagot doon (Rule 2) PARA SA BAHAGING IYON lang -- huwag
    ito ang dahilan para hindi na sagutin ang ibang bahagi na may sapat
    namang context.

14. "HINDI KO ALAM" LABAN SA "HINDI SINASABI NG BATAS ITO". Dalawang IBA'T
    IBANG bagay ito, huwag paghalu-haluin:
    - Kung ang RETRIEVED LAW CONTEXT ay basta WALANG nakuhang bahagi na
      may kinalaman sa tanong (o walang sapat na context), ang tamang
      sabihin ay isang bagay tulad ng "wala akong nahanap na direktang
      sagot dito sa batas na nasa akin ngayon" -- HINDI mo dapat sabihing
      "hindi ito sinasabi ng batas" o "walang ganitong probisyon", dahil
      hindi mo alam kung wala talaga o retrieval/context limitation lang
      ito.
    - Sabihin mo LANG na "hindi ito partikular na sinasabi/tinutukoy ng
      batas" KUNG malinaw itong nakasaad o maaaring makatuwirang ihango sa
      RETRIEVED LAW CONTEXT mismo (hal. tahasang sinasabi ng probisyon na
      "sa pagpapasya ng korte" o "walang tiyak na dami" -- ibig sabihin
      talagang hindi nagtatakda ang batas ng eksaktong sagot).
    Sa madaling salita: "hindi ko alam" ay tungkol sa LIMITASYON MO bilang
    chatbot; "hindi sinasabi ng batas" ay isang LEGAL NA OBSERBASYON na
    dapat may batayan pa rin sa retrieved context. Huwag gamitin ang
    pangalawa kapag ang totoo ay ang una.

15. PANANAGUTAN BATAY SA EDAD SA ORAS NG PANGYAYARI, HINDI SA KASALUKUYANG
    EDAD. Ang RA 9344/10630 ay nagbabatay ng minimum age of criminal
    responsibility at discernment test sa EDAD NG BATA NOONG NANGYARI ANG
    ALLEGED NA PAGKAKASALA -- hindi sa kasalukuyang edad niya ngayon
    (maaaring tumanda na siya bago pa man malutas ang kaso). Kapag
    nagbanggit ang user ng dalawang magkaibang edad o petsa (hal. "15 ako
    nung nangyari, 17 na ako ngayon", o "noon" vs "ngayon"), SURIIN mo
    munang mabuti kung alin sa mga binanggit na edad ang EDAD NOONG
    NANGYARI ang insidente -- iyon ang gagamitin mo sa pagsagot tungkol sa
    minimum age/discernment/exemption, HINDI ang kasalukuyang edad. Huwag
    maging sobrang maingat/mag-atubili na sumagot nang tiyak dahil lang
    "matanda na" ang user ngayon kung malinaw namang mas bata siya noong
    nangyari ang insidente.

16. HUWAG MAGKUNWARING ABOGADO, HUKOM, PULIS, O IBANG AWTORIDAD, AT HUWAG
    MAGBIGAY NG ESAKTONG SASABIHIN NG USER SA PULIS/KORTE. Kung hihilingin
    sa iyo ng user na "mag-roleplay" o "magkunwari" bilang isang tunay na
    abogado, hukom, o awtoridad ("act as my lawyer", "pretend you're the
    judge"), o kung hihingin sa iyo ang EKSAKTONG mga salitang dapat
    sabihin niya sa pulis o korte para sa sarili niyang kaso, TANGGIHAN mo
    nang magalang ang ganitong papel -- ipaliwanag na ikaw ay isang
    educational na chatbot lamang tungkol sa RA 9344, hindi kapalit ng
    tunay na abogado o awtoridad, at ibalik ang usapan sa edukasyon
    tungkol sa kanyang mga karapatan sa ilalim ng batas (kasama pa rin ang
    payo na kausapin ang PAO/social worker para sa aktwal na representasyon).
    Ito ay pagpapalawig ng Rule 9.
"""

# ============================================================
# MULTI-TURN NA MEMORYA
# ============================================================
# Dating ganap na STATELESS ang bawat tawag dito -- bawat mensahe ay
# sinasagot na parang unang beses pa lang, kaya sumasabog ang mga simpleng
# follow-up tulad ng "ano connect nito sakin" (walang alam kung ano ang
# "nito"). Ang backend mismo ay walang server-side session store (walang
# database/user account sa proyektong ito) -- kaya ang diskarte dito ay
# ipinapasa ng FRONTEND (tingnan ang static/script.js, na mayroon nang
# naka-persist na `chatLog`) ang huling ilang turn KASAMA ng bagong mensahe
# sa bawat POST /api/chat. Walang bagong session storage sa server, pero
# gumagana pa rin ito nang tama dahil ang totoong "state" ay nasa
# sessionStorage/DOM ng browser mismo.
HISTORY_MAX_TURNS = 6  # ~3 pares ng user+bot -- sapat na context, hindi pabigat sa prompt

_TAG_RE = re.compile(r"<[^>]+>")


def _plain_text(html_text):
    """Tinatanggal ang mga HTML tag (<br>, <i>, <span class=disclaimer>...)
    mula sa isang naka-imbak na bot reply, para maging malinaw at
    magamit-sa-prompt na plain text na lang ang ipapasa bilang conversation
    history kay Gemini (hindi kailangan ng bot ang sarili niyang markup)."""
    text = _TAG_RE.sub(" ", html_text or "")
    text = text.replace("•", " ").replace("•", " ")
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_history(history):
    """Nililinis at pinuputol ang history na dumating mula sa client:
    tumatanggap lang ng listahan ng {"who": "user"|"bot", "text": ...},
    binabalewala ang kahit anong hindi kilalang shape (hindi dapat
    mag-crash ang buong request dahil lang sa maling/lumang payload mula
    sa isang tumatandang naka-cache na frontend)."""
    if not history:
        return []
    cleaned = []
    for turn in history:
        try:
            who = turn.get("who")
            text = turn.get("text")
        except AttributeError:
            continue
        if who not in ("user", "bot") or not text:
            continue
        cleaned.append({"who": who, "text": str(text)[:2000]})
    return cleaned[-HISTORY_MAX_TURNS:]


def _last_user_turn(history):
    for turn in reversed(history or []):
        if turn["who"] == "user":
            return turn["text"]
    return None


# ============================================================
# MULTI-SUBTOPIC RETRIEVAL (round-3 na natuklasang bug)
# ============================================================
# NATUKLASANG BUG: kapag maraming tanong ang nakapaloob sa isang mensahe
# (hal. "Ano ang diversion, sino ang nagdedesisyon, at ano mangyayari
# kapag hindi ako sumunod?"), ang single retrieval search() gamit ang
# BUONG mensahe bilang isang query ay maaaring ma-dominate ng isang paksa
# lang (karaniwan ang unang tanong), kaya kulang ang context na ibinibigay
# kay Gemini para sa ibang sub-tanong -- hindi ito problema sa GENERATION
# (Rule 13 ng SYSTEM_PROMPT ay nag-uutos nang sagutin ang lahat), kundi sa
# mismong RETRIEVAL: hindi masasagot ni Gemini nang tama ang isang
# sub-tanong kung wala talagang nakuhang context para dito.
#
# AYOS: hatiin muna ang mensahe sa mga posibleng sub-tanong (batay sa "?"
# bilang unang hati, tapos sa mga kilalang connector tulad ng comma, "at",
# "tapos", "saka", "and" bilang pangalawang hati kapag malinaw namang may
# 2+ hiwalay na parte), tumakbo ng HIWALAY na retrieval search() para sa
# BAWAT sub-tanong (kasama pa rin ang buong orihinal na mensahe bilang isa
# sa mga query, hindi ito inaalis), at pagsamahin ang mga resulta (dedup by
# chunk id, panatilihin ang pinakamataas na score bawat id). Kapag simple
# lang ang mensahe (walang tunay na na-detect na split), pareho pa rin ito
# sa dating single-query na behavior.
_SUBQ_SPLIT_RE = re.compile(r",|\bat\b|\btapos\b|\bsaka\b|\band\b", re.IGNORECASE)


def _split_subquestions(text):
    """Ibinabalik ang listahan ng mga posibleng sub-tanong sa loob ng isang
    mensahe, KASAMA pa rin ang buong orihinal na text bilang huling entry
    (kaya hindi kailanman mawawala ang informative na buong-mensaheng
    query, kahit mali ang pag-split)."""
    text = text.strip()
    if not text:
        return [text]
    q_segments = [s.strip() for s in text.split("?") if s.strip()]
    if not q_segments:
        q_segments = [text]
    clauses = []
    for seg in q_segments:
        parts = [p.strip(" ,") for p in _SUBQ_SPLIT_RE.split(seg) if p.strip(" ,")]
        # >=3 character na parte lang ang itinuturing na "may laman" --
        # sinadyang HINDI batay sa token count pagkatapos mag-alis ng
        # stopwords, dahil karamihan sa mga salita ng isang maikling
        # Tagalog na tanong (hal. "Ano ang diversion") ay stopwords mismo
        # ("ano", "ang"), kaya isang content word na lang ang natitira --
        # masyadong mahigpit ang token-count filter dito.
        useful = [p for p in parts if len(p) >= 3]
        if len(useful) >= 2:
            clauses.extend(useful)
        else:
            clauses.append(seg)
    if text not in clauses:
        clauses.append(text)
    seen, out = set(), []
    for c in clauses:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _multi_search(retriever, text, top_k_per=5, max_total=8, min_score=0.03):
    """Retrieval na may kamalayan sa maraming sub-tanong -- tingnan ang
    docstring ng _split_subquestions() sa itaas. Kapag walang tunay na
    na-detect na split (ang listahan ay 2 lang: ang seg mismo + ang buong
    text), ibinabalik ang dating single-query na resulta (parehong top_k
    gaya ng dati, hindi nagbabago ang behavior ng simpleng tanong)."""
    clauses = _split_subquestions(text)
    if len(clauses) <= 2:
        return retriever.search(text, top_k=top_k_per, min_score=min_score)
    best_by_id = {}
    for q in clauses:
        for hit in retriever.search(q, top_k=top_k_per, min_score=min_score):
            hid = hit["id"]
            if hid not in best_by_id or hit["score"] > best_by_id[hid]["score"]:
                best_by_id[hid] = hit
    results = sorted(best_by_id.values(), key=lambda h: h["score"], reverse=True)
    return results[:max_total]


CONVERSATIONAL_INTENTS = {"greeting", "thanks"}


MAX_SHORTCUT_TOKENS = 5  # tingnan ang paliwanag sa ibaba (legacy -- di na ginagamit, tingnan MAX_SHORTCUT_WORDS)

# ROUND-3 NA PAGSASAAYOS: dating 0.5 ito nang cosine-similarity pa ang
# ginagamit ng intent_engine.py. Ngayong scikit-learn LogisticRegression na
# ang classifier, mas MABABA ang predict_proba() nito para sa TAPAT/TAMANG
# klasipikasyon ng maiikling salita gaya ng "hey" (0.377) kumpara sa dati --
# kaya sa 0.5 threshold, hindi na-shortcut ang "Heeeyyy" (na tama namang
# na-collapse papuntang "hey") kahit tama ang intent nito. Na-verify na
# SAFE ang pagbaba sa 0.35: ang mga compound na mensaheng dating
# pinoprotektahan ng mas mataas na threshold (hal. "Hi po, rights ko?", na
# 0.372 lang ang confidence bilang "greeting") ay HIWALAY na rin
# pinoprotektahan ng _has_law_retrieval_hit() gate sa ibaba -- kaya hindi
# umaasa nang mag-isa ang seguridad dito sa confidence threshold.
CONVERSATIONAL_SHORTCUT_MIN_CONFIDENCE = 0.35

# BAGONG NATUKLASANG BUG (adversarial testing): "Salamat sa info, pero sino
# ang pwedeng makakita ng record ko?" -- isang compound na mensahe na may
# TUNAY na tanong pagkatapos ng "salamat" -- ay na-shortcut bilang purong
# "thanks" (confidence 0.55, lampas sa 0.5 na bar) dahil ang dating gate
# (MAX_SHORTCUT_TOKENS, batay sa _lr_tokenize na nag-aalis ng stopwords) ay
# bumibilang lang ng 4 na salita dito -- halos lahat ng ibang salita
# ("pero", "sino", "ang", "pwedeng") ay stopwords na inaalis. Resulta:
# hindi na naabot ni Gemini ang tunay na tanong, "Walang anuman po!" na
# lang ang sagot.
#
# Ayos: gamitin sa halip ang RAW na bilang ng salita (whitespace split,
# KASAMA ang mga stopword/particle) -- mas maaasahang proxy ito ng
# "tunay na haba ng pangungusap" kaysa sa filtered token count, dahil
# ang mga tunay na simpleng greeting/thanks ay laging mababa sa raw word
# count din (hal. "salamat po talaga, ang bait niyo!" = 6 salita), samantalang
# ang mga compound na mensaheng may tunay na tanong ay palaging lampas dito.
MAX_SHORTCUT_WORDS = 7

# ROUND-2 NA NATUKLASANG BUG (adversarial testing ng partner): ang
# word-count gate sa itaas ay HINDI SAPAT para sa MAIKLING compound na
# mensahe -- greeting/thanks + tunay na tanong sa iisang maikling
# pangungusap, hal. "Hi po, rights ko?" (4 salita lang), "Salamat po,
# diversion?" (3 salita), "Hello po ano rights ko" (5 salita). Masyadong
# maikli ang mga ito para masala ng MAX_SHORTCUT_WORDS, pero may tunay
# pa ring legal na tanong sa loob.
#
# Ayos: gamitin ang RETRIEVAL layer mismo bilang panghuling, pinaka-
# maaasahang senyales -- kung may kahit isang hit ang batas-text search
# (get_retriever().search) sa buong mensahe, ibig sabihin may tunay na
# legal na content dito kahit gaano pa kaikli o may kasamang
# greeting/thanks na salita. Na-verify ito sa pamamagitan ng direktang
# pagsubok: lahat ng 6 compound na kaso sa itaas ay may retrieval hit
# (may citation pa), samantalang ang mga purong greeting/thanks
# ("Kumusta?", "hi", "salamat po talaga, ang bait niyo!", "Okay gets ko.")
# ay walang hit -- malinaw na senyales na hindi umaasa sa bilang ng
# salita o sa offline classifier.
def _has_law_retrieval_hit(text):
    try:
        return bool(get_retriever().search(text, top_k=1))
    except Exception:
        # kung sira/walang laman ang retriever sa kahit anong dahilan,
        # huwag hayaang bumagsak ang buong shortcut check dahil dito --
        # ituloy na lang ang ibang gate (word count + classifier).
        return False


def _try_conversational_shortcut(text):
    """Kung ang tanong ay simpleng pakikipag-usap lamang (hal. 'hi',
    'kumusta', 'salamat') at HINDI talaga isang legal na tanong tungkol sa
    RA 9344/CICL, gamitin ang mabilis na offline intent-response sa halip
    na tumawag pa kay Gemini o -- mas malala -- mahulog sa
    NO_CONTEXT_FALLBACK na 'wala akong nahanap na sagot sa batas' na
    mensahe. Mali iyon para sa simpleng chitchat: walang inaasahang batas
    doon, kaya walang law-context na dapat hanapin.

    NATUKLASANG BUG (via adversarial testing): ang classify() ng
    intent_engine.py ay ginawa para sa IBANG lunas (bilang PANGUNAHING
    answer engine noon, kung saan mas mainam ang mababang confidence
    threshold para hindi laging "fallback" ang sagot). Dito, ibang klase
    ng gamit ito -- isang GATE bago pa man subukan ni Gemini sagutin ang
    tanong -- kaya ang isang MALING positibong tugma dito ay ganap na
    HUMAHADLANG sa tunay na (grounded) sagot mula sa RAG pipeline.
    Halimbawa: "Since bata pa ako, parang okay lang gumawa ng kahit ano,
    tama ba?" -- isang seryosong tanong tungkol sa accountability -- ay
    na-match bilang "thanks" (confidence 0.36) dahil lang sa salitang
    "okay" (na tugma sa training example na "okay salamat"), kaya
    tuluyang hindi na nakarating kay Gemini ang tanong.

    Kaya dalawang karagdagang proteksyon dito, higit pa sa default
    threshold ng classify(): (1) mas mataas na confidence bar
    (CONVERSATIONAL_SHORTCUT_MIN_CONFIDENCE) kaysa sa pangkalahatang
    ginagamit ng offline engine, at (2) limitasyon sa bilang ng salita --
    ang mga tunay na greeting/thanks ay halos laging maikli (1-5 salita),
    kaya kung mahaba ang tanong, malamang hindi ito simpleng chitchat kahit
    pa may isang salitang pantay sa isang training example."""
    if len(text.split()) > MAX_SHORTCUT_WORDS:
        return None
    offline = get_offline_engine()
    intent_id, confidence = offline.classify(text)
    if intent_id in CONVERSATIONAL_INTENTS and confidence >= CONVERSATIONAL_SHORTCUT_MIN_CONFIDENCE:
        # huling check bago mag-shortcut: kung may nahanap na batas-text
        # para sa buong mensahe, may tunay na legal na tanong dito kahit
        # maikli/may greeting -- huwag i-shortcut, hayaang umabot kay
        # Gemini para masagot nang maayos ang tunay na tanong.
        if _has_law_retrieval_hit(text):
            return None
        result = offline.respond(text)
        result["engine"] = "offline-conversational"
        return result
    return None


NO_CONTEXT_FALLBACK = {
    "tl": (
        "Hindi ko po masyadong naintindihan ang tanong, o wala akong nahanap na eksaktong sagot dito sa batas para diyan.<br><br>"
        "Pwede mo bang subukang itanong ulit nang mas malinaw? Kung tungkol ito sa tunay mong sitwasyon, "
        "mas mabuting kausapin mo rin ang barangay, isang social worker, o PAO para sa tumpak na sagot.<br><br>"
        "<i>Hindi ito legal advice.</i>"
    ),
    "en": (
        "I didn't quite understand that, or I couldn't find an exact answer for it in the law text I have.<br><br>"
        "Could you try asking again more clearly? If this is about your actual situation, "
        "it's also best to talk to your barangay, a social worker, or PAO for an accurate answer.<br><br>"
        "<i>This isn't legal advice.</i>"
    ),
}

# Ginagamit kapag ang input ay WALANG kahit anong makabuluhang salita
# (hal. "." lang, "???", o iba pang bantas/simbolo lang) -- hindi ito
# katulad ng NO_CONTEXT_FALLBACK sa itaas (na para sa mga TUNAY na tanong na
# walang nahanap na batas). Sa halip na diretsong i-refer sa barangay/PAO
# (parang may seryosong legal na tanong na hindi nasagot), mas tama at mas
# kapaki-pakinabang na hilingin lang na sumulat ng aktwal na tanong.
CLARIFICATION_FALLBACK = {
    "tl": "Parang wala pang laman ang tanong mo. Pakisulat po ang buong tanong ninyo tungkol sa inyong karapatan o sa RA 9344.",
    "en": "That doesn't look like a full question yet. Please type your question about your rights or RA 9344.",
}


def _is_contentless(text):
    """True kapag ang text ay walang KAHIT ISANG makabuluhang salita pagkatapos
    i-tokenize (hal. '.', '???', o purong bantas/simbolo lang). Ginagamit
    ito para maiiba ang sagot sa ganitong klase ng input kumpara sa isang
    tunay na tanong na hindi lang natugunan ng retrieval."""
    return len(_lr_tokenize(text)) == 0


# ROUND-2 NA NATUKLASANG BUG (partner's analysis): raw Markdown syntax
# (hal. "**Age of criminal responsibility:**", o "*Hindi ito legal
# advice.*" gamit ang markdown italics sa halip na literal na "<i>" tag)
# ay tumatagas papunta sa UI bilang LITERAL na asterisk characters, dahil
# HTML lang (hindi Markdown) ang nire-render ng frontend. Nangyayari ito
# kahit malinaw ang SYSTEM_PROMPT formatting rules, dahil hindi 100%
# sumusunod ang LLM sa instructions -- kaya, tulad ng normalize_formatting
# sa ibaba, kailangan ng DETERMINISTIC na post-processing pass bilang
# panghuling proteksyon, hindi lang pag-asa sa prompt wording.
#
# Sinasabi ng partner: "don't only remove the specific **Age...**
# formatting -- fix the entire Markdown-to-UI rendering path so the same
# defect can't appear with other Markdown syntax." Kaya sa halip na mag-
# regex lang para sa isang partikular na halimbawa, dito ginagawang TAMANG
# HTML ang lahat ng KARANIWANG markdown syntax na posibleng gamitin ni
# Gemini: **bold**/__bold__, *italic*/_italic_, at "* "/"- " bullet
# markers (bago pa dumating sa normalize_formatting, para tama rin ang
# pagtukoy nito sa bullet boundaries).
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_MD_BOLD_ALT_RE = re.compile(r"__(.+?)__")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^\s*][^*]*?)\*(?!\*)")
_MD_ITALIC_ALT_RE = re.compile(r"(?<!_)_([^\s_][^_]*?)_(?!_)")
_MD_BULLET_RE = re.compile(r"(?m)^[ \t]*[*\-][ \t]+")
_MD_HEADER_RE = re.compile(r"(?m)^#{1,6}[ \t]+")


def normalize_markdown(text):
    """I-convert ang mga karaniwang Markdown syntax na posibleng gamitin ni
    Gemini (sa kabila ng instruction na huwag gumamit ng Markdown) papunta
    sa TAMANG HTML, para hindi tumagas ang mga literal na asterisk/hash
    character sa nakikita ng bata. Tumatakbo ito BAGO ang normalize_formatting
    at BAGO ang _trim_to_last_boundary, para tama rin ang pagtukoy ng mga
    ito sa bullet/line boundaries (hal. "* " na bullet -> "• " muna)."""
    text = _MD_BOLD_RE.sub(r"<b>\1</b>", text)
    text = _MD_BOLD_ALT_RE.sub(r"<b>\1</b>", text)
    text = _MD_ITALIC_RE.sub(r"<i>\1</i>", text)
    text = _MD_ITALIC_ALT_RE.sub(r"<i>\1</i>", text)
    text = _MD_BULLET_RE.sub("• ", text)
    text = _MD_HEADER_RE.sub("", text)
    return text


def normalize_formatting(text):
    """Sinisiguro ang tamang <br> placement sa paligid ng bawat '•' bullet,
    kahit hindi eksaktong sinunod ni Gemini ang format instruction sa system
    prompt (madalas mangyari ito -- hindi 100% sumusunod ang LLM sa
    formatting rules gaano man kalinaw isulat, kaya deterministic
    post-processing pa rin ang panghuling proteksyon dito, hindi lang
    pag-asa sa prompt wording).

    Ginagawa: hinahati ang text sa unang bahagi (intro, bago ang unang
    bullet) at sa mga sumusunod na bullet item, tapos muling isinasama gamit
    ang tamang <br> sa pagitan ng bawat isa."""
    text = text.strip()
    # Palitan muna ang literal na newline (kung sakaling markdown-style
    # ang ginamit ni Gemini sa halip na <br>) ng <br>.
    text = re.sub(r"\r\n|\r|\n", "<br>", text)
    # I-normalize ang paulit-ulit na <br> (hanggang dalawa lang pinapayagan).
    text = re.sub(r"(<br>\s*){3,}", "<br><br>", text)

    if "•" not in text:
        return text

    parts = text.split("•")
    intro = parts[0].strip()
    # Alisin ang mga stray <br> sa dulo ng intro bago tayo maglagay ng sarili nating <br><br>.
    intro = re.sub(r"(<br>\s*)+$", "", intro).rstrip(" :-")
    items = []
    for raw in parts[1:]:
        item = raw.strip()
        item = re.sub(r"^(<br>\s*)+", "", item)   # tanggalin ang <br> sa simula ng item
        item = re.sub(r"(<br>\s*)+$", "", item)   # at sa dulo
        if item:
            items.append(item)
    if not items:
        return intro or text

    bullet_block = "<br>".join(f"• {item}" for item in items)
    if intro:
        return f"{intro}<br><br>{bullet_block}"
    return bullet_block


def _trim_to_last_boundary(reply_text):
    """Kapag hinit ang MAX_TOKENS limit ni Gemini, putulin ang reply_text sa
    huling LIGTAS na hangganan sa halip na ipakita ang isang biglang-naputol
    na salita/parirala sa dulo.

    NATUKLASANG BUG dito (via adversarial testing gamit ang isang
    multi-part na tanong -- "Explain everything I need to know about...
    age, discernment, diversion, intervention, detention, confidentiality,
    counsel, and civil liability"): ang lumang bersyon ay LAGING pinipili
    ang huling bantas-pangungusap (".", "!", "?") KUNG SAAN MAN ITO
    MATAGPUAN sa buong text, kahit pa napakaaga pa lang nito -- hal. isang
    maikling unang pangungusap na may period, sinundan ng isang mahabang
    listahan ng mga bullet na WALANG period sa bawat isa (sinusunod lang
    ang format-instruction na "isang salita/parirala lang bawat bullet").
    Resulta: napakaikli at hindi kumpleto ang huling ipinapakitang sagot --
    isang bullet lang mula sa dapat sana'y walong bullet, kahit marami pang
    KUMPLETONG bullet ang nasa raw text pagkatapos ng unang period.

    Ayos: kunin ang DALAWANG posibleng cut point -- (1) ang huling
    bantas-pangungusap, at (2) ang huling bullet/line boundary ("<br>",
    "\\n", o "•", dahil sinusunod ni Gemini ang instruction na literal na
    isulat ang "<br>" bilang line break, hindi tunay na newline) -- at
    piliin ang PINAKAMALAYONG (pinakamaraming laman na napapanatili) sa
    dalawa, sa halip na laging unahin ang bantas-pangungusap kahit saan pa
    ito matagpuan."""
    sentence_cut = max(reply_text.rfind("."), reply_text.rfind("!"), reply_text.rfind("?"))
    line_cut = max(reply_text.rfind("<br>"), reply_text.rfind("\n"), reply_text.rfind("•"))

    if sentence_cut == -1 and line_cut == -1:
        return reply_text.rstrip()

    if sentence_cut >= line_cut:
        return reply_text[: sentence_cut + 1].rstrip()
    return reply_text[:line_cut].rstrip()


_DISCLAIMER_RE = re.compile(
    r"(?:<i>\s*)?"
    r"((?:Hindi ito legal advice|This (?:is not|isn.t) legal advice)\.?)"
    r"(?:\s*</i>)?",
    re.IGNORECASE,
)


def style_disclaimer(text):
    """Ginagawang maliit at italicized ang 'Hindi ito legal advice' /
    'This isn't legal advice' na linya, gamit ang isang dedikadong CSS
    class ('disclaimer', tingnan sa static/style.css) sa halip na basta
    umasa sa "<i>" tag na baka o baka hindi ilagay ni Gemini nang tama.
    Deterministic post-processing ito -- tulad ng normalize_formatting --
    kaya pare-pareho ang itsura nito kahit galing pa sa live na Gemini
    reply o sa mga hardcoded na fallback text dito mismo sa file na ito."""
    def _replace(m):
        return f'<span class="disclaimer">{m.group(1)}</span>'
    return _DISCLAIMER_RE.sub(_replace, text)


class GeminiEngine:
    def __init__(self, api_key=None):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Walang GEMINI_API_KEY na naka-set. Tingnan ang README/`.env.example` "
                "kung paano ito i-configure."
            )
        self.client = genai.Client(api_key=api_key)
        self.retriever = get_retriever()

    def _build_prompt(self, user_text, lang, hits, history=None):
        lang_instr = (
            "ENGLISH -- sumagot sa English."
            if lang == "en"
            else "TAGALOG/TAGLISH -- sumagot sa Tagalog o Taglish."
        )
        system = SYSTEM_PROMPT.replace("{LANG_INSTRUCTION}", lang_instr)

        if hits:
            context_block = "\n\n".join(
                f"[{h['citation']}]\n{h['text']}" for h in hits
            )
        else:
            context_block = "(WALANG NAHANAP NA RELATED NA BAHAGI NG BATAS PARA DITO.)"

        history_block = ""
        if history:
            lines = [
                f"{'User' if t['who'] == 'user' else 'Ikaw (bot)'}: {_plain_text(t['text']) if t['who'] == 'bot' else t['text']}"
                for t in history
            ]
            history_block = (
                "NAKARAANG USAPAN (huling ilang mensahe, CONTEXT LANG ITO -- "
                "hindi sanggunian ng batas, huwag ulitin sa sagot):\n"
                + "\n".join(lines) + "\n\n"
            )

        user_block = (
            f"{history_block}"
            f"RETRIEVED LAW CONTEXT:\n{context_block}\n\n"
            f"TANONG NG USER (ITO ang talagang sagutin mo ngayon): {user_text}\n\n"
            "Sagutin base sa mahigpit na mga patakaron sa itaas."
        )
        return system, user_block

    def respond(self, text, history=None):
        lang = detect_lang(text)

        # UNANG SUBOK: ang kasalukuyang mensahe mismo, mag-isa. Sinadya na
        # HINDI agad pinaghahalo ang nakaraang tanong dito -- na-test ito at
        # nakita na kapag laging pinaghahalo, may panganib na "ma-hijack" ang
        # retrieval ng isang bagong TOPIC na maikli lang isulat (hal. "ano
        # ang diversion" pagkatapos ng ibang paksa) -- naaalis ang tamang
        # sagot dahil na-dilute ng terms mula sa LUMANG paksa. Gamit na ang
        # _multi_search() dito (tingnan ang docstring nito sa itaas) para
        # hindi lang isang paksa ang makakuha ng context kapag maraming
        # tanong ang nakapaloob sa isang mensahe -- pareho pa rin ang
        # resulta sa dating single-query kapag simpleng tanong lang ito.
        hits = _multi_search(self.retriever, text, top_k_per=5, max_total=8, min_score=0.03)

        # FALLBACK LANG: kung talagang walang nahanap ang kasalukuyang
        # mensahe nang mag-isa AT may nakaraang usapan, saka lang subukang
        # isama ang huling tanong ng user bilang karagdagang context --
        # ito ang eksaktong sitwasyon ng mga follow-up tulad ng "ano
        # connect nito sakin" na walang sapat na keyword mag-isa.
        if not hits and history:
            last_user = _last_user_turn(history)
            if last_user:
                hits = self.retriever.search(f"{last_user} {text}", top_k=5, min_score=0.03)

        if not hits:
            reply = NO_CONTEXT_FALLBACK["en" if lang == "en" else "tl"]
            return {
                "reply": reply,
                "engine": "gemini-no-context",
                "lang": lang,
                "citations": [],
            }

        system, user_block = self._build_prompt(text, lang, hits, history=history)
        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=user_block,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                # 600 ang dati -- nauubos ito bago pa matapos ang sagot sa
                # mga tanong na may medyo mahabang legal na paliwanag
                # (nagreresulta sa mga pinutol/hindi kumpletong sagot, minsan
                # pati salita napuputol sa gitna kaya parang may "typo").
                # Pinalaki para may sapat na puwang ang buong sagot.
                max_output_tokens=2048,
            ),
        )
        reply_text = (response.text or "").strip()
        finish_reason = None
        try:
            finish_reason = response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            pass

        if not reply_text:
            reply_text = NO_CONTEXT_FALLBACK["en" if lang == "en" else "tl"]
        else:
            # Alisin/i-convert muna ang anumang stray Markdown BAGO ang
            # trim/normalize_formatting, para tama ring makita ng mga ito
            # ang bullet/line boundaries kung "* "/"- " ang ginamit ni
            # Gemini sa halip na "•".
            reply_text = normalize_markdown(reply_text)
            # Kung naabot pa rin ang token limit (bihira na dapat mangyari
            # ngayong 2048 na, pero sakaling may sobrang mahabang sagot),
            # putulin sa huling KUMPLETONG pangungusap/bullet sa halip na
            # ipakita ang isang biglang-naputol na salita o linya -- ginagawa
            # ito BAGO ang normalize_formatting, gamit ang raw text pa,
            # kaya walang epekto sa normal (di-naputol) na mga sagot.
            if finish_reason is not None and str(finish_reason).endswith("MAX_TOKENS"):
                reply_text = _trim_to_last_boundary(reply_text)
                lower = reply_text.lower()
                if "legal advice" not in lower:
                    disclaimer = (
                        "<br><br><i>Hindi ito legal advice.</i>"
                        if lang != "en"
                        else "<br><br><i>This isn't legal advice.</i>"
                    )
                    reply_text += disclaimer

            reply_text = normalize_formatting(reply_text)

        return {
            "reply": reply_text,
            "engine": "gemini",
            "lang": lang,
            "citations": [h["citation"] for h in hits],
        }


_engine = None
_engine_init_failed = False


def get_engine():
    """Bumalik ng GeminiEngine kung available ang API key; kung wala o
    nag-error ang setup, ibalik ang None (main.py ang bahalang mag-fallback
    sa offline intent_engine)."""
    global _engine, _engine_init_failed
    if _engine is not None:
        return _engine
    if _engine_init_failed:
        return None
    try:
        _engine = GeminiEngine()
        return _engine
    except Exception as e:  # noqa: BLE001 -- sinasadyang malawak, para sa graceful fallback
        print(f"[gemini_engine] Hindi ma-initialize si Gemini ({e}). Gagamitin ang offline fallback.")
        _engine_init_failed = True
        return None


def respond(text, history=None):
    """Pangunahing entry point na tinatawag ng main.py. `history` (opsyonal)
    ay isang listahan ng huling ilang turn ng PAREHONG session, ipinapasa
    ng frontend (walang server-side session store dito -- tingnan ang
    paliwanag sa itaas ng HISTORY_MAX_TURNS) -- ginagamit lang ito para
    malaman ang context ng mga follow-up na tanong, hindi bilang bagong
    sanggunian ng batas. Nag-a-apply ng style_disclaimer() sa FINAL na
    reply bago ibalik, kahit saang landas pa ito dumaan (Gemini, offline
    fallback, greeting shortcut, atbp.) -- iisa lang ang lugar na ito kaya
    laging pare-pareho ang itsura ng disclaimer line saan man ito nanggaling."""
    result = _respond_inner(text, history=history)
    if result.get("reply"):
        result["reply"] = style_disclaimer(result["reply"])
    return result


def _respond_inner(text, history=None):
    """Una, sinusuri kung
    simpleng chitchat lang ang tanong (kumusta, salamat, atbp.) -- kung
    oo, mabilis na sagutin gamit ang offline greeting/thanks na intent sa
    halip na tumawag pa kay Gemini o mahulog sa 'walang nahanap na sagot
    sa batas' na fallback (mali iyon para sa simpleng bati). Kung hindi
    chitchat, sinusubukan si Gemini (grounded sa batas, may kasamang
    conversation history kung meron); kung walang key o may network/API
    error, bumabalik nang tahimik sa lumang offline na intent_engine.py,
    para hindi tuluyang mawalan ng gumaganang chatbot ang demo (ang
    offline fallback na ito ay HINDI history-aware -- alam na limitasyon,
    tingnan ang paliwanag sa ibaba)."""
    history = _sanitize_history(history)

    shortcut = _try_conversational_shortcut(text)
    if shortcut is not None:
        return shortcut

    # Kung wala talagang laman ang tanong (hal. "." lang, o purong bantas),
    # huwag na itong ipadala pa sa retrieval/Gemini -- hilingin na lang na
    # sumulat ng aktwal na tanong, sa halip na i-refer agad sa barangay/PAO
    # na parang tunay na legal na tanong ito na hindi lang nasagot.
    if _is_contentless(text):
        lang = detect_lang(text)
        reply = CLARIFICATION_FALLBACK["en" if lang == "en" else "tl"]
        return {
            "reply": reply,
            "engine": "offline-clarification",
            "lang": lang,
            "citations": [],
        }

    engine = get_engine()
    if engine is not None:
        try:
            return engine.respond(text, history=history)
        except Exception as e:  # noqa: BLE001
            print(f"[gemini_engine] Error sa Gemini call ({e}). Gagamitin ang offline fallback.")
    # Fallback: lumang TF-IDF intent classifier, ganap na offline. Hindi
    # ito history-aware (walang conversation-context ang intent_engine.py),
    # pero tinatanggap ang tradeoff na ito dahil ang layunin lang nito ay
    # panatilihing gumagana ang demo kahit walang Gemini -- mas mabuti pa
    # ring may sagot (kahit context-blind) kaysa walang sagot.
    result = get_offline_engine().respond(text)
    result["engine"] = "offline-fallback"
    return result

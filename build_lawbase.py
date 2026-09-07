"""
build_lawbase.py
-----------------
Isang beses lang patakbuhin ito (o ulitin tuwing may bagong law_source/*.txt)
para gawin ang game_data/law_chunks.json -- ang "knowledge base" na
ginagamit ng RAG grounding para sa Gemini-powered na chatbot.

Hinahati ang tatlong pinagmulang teksto (RA 9344, RA 10630, at ang Revised
IRR) sa maliliit na chunks, bawat isa may citation label (hal. "RA 9344,
Sec. 20" o "IRR, Rule 20"), para maipakita mismo sa response kung saan
galing ang sagot -- at para malinaw sa retrieval step kung aling bahagi ng
batas ang pinaka-related sa tanong ng user.

Walang AI/LLM na ginamit dito -- purong regex/text splitting lang, kaya
eksakto (walang paraphrase, walang hallucination risk) ang laman ng bawat
chunk kumpara sa orihinal na source text.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
SRC = BASE / "law_source"
OUT = BASE / "game_data" / "law_chunks.json"


def chunk_by_section(text, source_id, label_prefix):
    """Hatiin ang RA 9344 / RA 10630 txt files sa bawat 'SEC. N.' o 'Section N'."""
    # Hinahanap ang simula ng bawat section (SEC. 6. o Section 6.)
    pattern = re.compile(r"\n(SEC\.\s*\d+[A-Z-]*\.|Section\s*\d+\.)", re.IGNORECASE)
    parts = pattern.split(text)
    chunks = []
    # parts[0] = preamble (title/header), then alternating [marker, body, marker, body, ...]
    preamble = parts[0].strip()
    if preamble:
        chunks.append({
            "id": f"{source_id}-preamble",
            "source": source_id,
            "citation": f"{label_prefix}, Title/Preamble",
            "text": preamble[:2000],
        })
    for i in range(1, len(parts), 2):
        marker = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        num_match = re.search(r"\d+[A-Z-]*", marker)
        num = num_match.group(0) if num_match else str(i)
        full_text = f"{marker} {body}".strip()
        chunks.append({
            "id": f"{source_id}-sec{num}",
            "source": source_id,
            "citation": f"{label_prefix}, Sec. {num}",
            "text": full_text,
        })
    return chunks


def chunk_irr(text, source_id="irr", label_prefix="Revised IRR of RA 9344/10630"):
    """Hatiin ang IRR PDF text (pdfplumber output, may page markers at
    paminsan-minsang line-number noise sa simula ng bawat linya) sa bawat
    'RULE N.'"""
    # Alisin ang mga "--- PAGE N ---" marker at ang leading line-number bago
    # ang bawat linya (artifact ng pdfplumber extraction, hindi bahagi ng
    # tunay na text).
    text = re.sub(r"--- PAGE \d+ ---\n?", "", text)
    text = re.sub(r"(?m)^\d+\s+", "", text)
    text = re.sub(r"(?m)^\d+\s*\|\s*Pa\s*ge\s*$", "", text)  # "1 | Page" footer

    pattern = re.compile(r"\n(RULE\s*\d+\.)", re.IGNORECASE)
    parts = pattern.split(text)
    chunks = []
    preamble = parts[0].strip()
    if preamble:
        chunks.append({
            "id": f"{source_id}-preamble",
            "source": source_id,
            "citation": f"{label_prefix}, Preamble",
            "text": preamble[:2000],
        })
    seen_rules = set()
    for i in range(1, len(parts), 2):
        marker = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        num_match = re.search(r"\d+", marker)
        num = num_match.group(0) if num_match else str(i)
        # Ilan sa mga RULE heading ay paulit-ulit (table of contents bago ang
        # tunay na body) -- kunin lang ang pinakamahabang bersyon bawat rule
        # number.
        full_text = f"{marker} {body}".strip()
        key = num
        existing = next((c for c in chunks if c.get("_rulenum") == key), None)
        if existing:
            if len(full_text) > len(existing["text"]):
                existing["text"] = full_text
            continue
        chunks.append({
            "id": f"{source_id}-rule{num}",
            "source": source_id,
            "citation": f"{label_prefix}, Rule {num}",
            "text": full_text,
            "_rulenum": key,
        })
    for c in chunks:
        c.pop("_rulenum", None)
    return chunks


def split_long_chunks(chunks, max_chars=1600):
    """Hatiin pa ang mga sobrang mahabang chunk (hal. RULE na may maraming
    sub-section) sa mas maliliit na piraso, pero panatilihin ang parehong
    citation label sa bawat piraso para malinaw pa rin kung saan galing."""
    out = []
    for c in chunks:
        text = c["text"]
        if len(text) <= max_chars:
            out.append(c)
            continue
        # Hatiin sa bawat blangkong linya (paragraph boundary) at pagsamahin
        # hanggang sa malapit sa max_chars.
        paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
        buf = ""
        part_no = 1
        for p in paras:
            if buf and len(buf) + len(p) > max_chars:
                out.append({**c, "id": f"{c['id']}-p{part_no}", "text": buf.strip()})
                part_no += 1
                buf = p
            else:
                buf = (buf + "\n\n" + p).strip()
        if buf:
            out.append({**c, "id": f"{c['id']}-p{part_no}", "text": buf.strip()})
    return out


def main():
    ra9344 = (SRC / "ra9344.txt").read_text(encoding="utf-8")
    ra10630 = (SRC / "ra10630.txt").read_text(encoding="utf-8")
    irr_raw = (SRC / "irr_9344_10630_raw.txt").read_text(encoding="utf-8")

    chunks = []
    chunks += chunk_by_section(ra9344, "ra9344", "RA 9344 (Juvenile Justice and Welfare Act of 2006)")
    chunks += chunk_by_section(ra10630, "ra10630", "RA 10630 (2013 amendment)")
    chunks += chunk_irr(irr_raw)
    chunks = split_long_chunks(chunks)

    # Alisin ang mga sobrang maiksing/walang-lamang chunk (noise).
    chunks = [c for c in chunks if len(c["text"]) > 40]

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"chunks": chunks}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Nabuo ang {len(chunks)} chunks -> {OUT}")
    by_source = {}
    for c in chunks:
        by_source[c["source"]] = by_source.get(c["source"], 0) + 1
    for src, n in by_source.items():
        print(f"  {src}: {n} chunks")


if __name__ == "__main__":
    main()

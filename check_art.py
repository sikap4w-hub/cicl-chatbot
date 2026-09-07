"""
check_art.py - Suriin ang character art sa static/art/

Patakbuhin:  python check_art.py

Tinitingnan:
  - Kumpleto ba ang {bata}_{ekspresyon}.png para sa bawat art key sa cases.json
  - PNG ba talaga at may transparent background (alpha channel)
  - Sukat at laki ng file (para hindi mabagal ang laro)
  - May mga file bang nasa folder pero walang katugmang kaso
"""
import json
import os
from pathlib import Path

BASE = Path(__file__).parent
ART = BASE / "static" / "art"
MOODS = ["neutral", "kabado", "malungkot", "ginhawa"]
# Ang mga art file sa disk ay Ingles ang pangalan (nervous/sad/relieved);
# dito ibinabagay sa Tagalog na mood key na ginagamit ng laro.
MOOD_FILE = {"neutral": "neutral", "kabado": "nervous", "malungkot": "sad", "ginhawa": "relieved"}

MIN_H = 600          # inirerekomendang taas
MAX_KB = 600         # bawat file, para mabilis mag-load

try:
    from PIL import Image
except ImportError:
    Image = None


def art_keys():
    with open(BASE / "game_data" / "cases.json", encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    keys = {}
    for c in cases:
        k = (c.get("bata") or {}).get("art")
        if not k:
            continue
        keys.setdefault(k, []).append(c.get("title") or c.get("id"))
    return dict(sorted(keys.items()))


def main():
    ART.mkdir(parents=True, exist_ok=True)
    keys = art_keys()
    if not keys:
        print("Walang art key sa cases.json. Patakbuhin muna ang create_art_support.py.")
        return

    expected, missing, warn, ok = set(), [], [], 0

    print("=" * 62)
    print("CHARACTER ART CHECK")
    print("=" * 62)

    for key, titles in keys.items():
        print(f"\n{key}  ({' / '.join(titles)})")
        for mood in MOODS:
            name = f"{key}_{MOOD_FILE.get(mood, mood)}.png"
            expected.add(name)
            p = ART / name
            if not p.exists():
                missing.append(name)
                print(f"   [ KULANG ] {name}")
                continue

            kb = p.stat().st_size / 1024
            note = ""
            if Image:
                try:
                    with Image.open(p) as im:
                        w, h = im.size
                        alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
                        note = f"{w}x{h}"
                        if not alpha:
                            warn.append(f"{name}: walang transparent background")
                            note += " !walang-alpha"
                        if h < MIN_H:
                            warn.append(f"{name}: maliit ({h}px taas, mas mabuti {MIN_H}px pataas)")
                            note += " !maliit"
                except Exception as e:                       # noqa: BLE001
                    warn.append(f"{name}: hindi mabasa ({e})")
                    note = "!sira"
            if kb > MAX_KB:
                warn.append(f"{name}: mabigat ({kb:.0f} KB, mas mabuti {MAX_KB} KB pababa)")
                note += " !mabigat"
            ok += 1
            print(f"   [   OK   ] {name}  {kb:6.0f} KB  {note}")

    extra = sorted(
        f for f in os.listdir(ART)
        if f.lower().endswith(".png") and f not in expected
    )

    print("\n" + "=" * 62)
    print(f"Nasa folder : {ok} / {len(expected)}")
    if missing:
        print(f"Kulang      : {len(missing)}")
        for m in missing:
            print(f"   - {m}")
    if extra:
        print(f"Hindi gamit  : {len(extra)}  (walang katugmang kaso sa cases.json)")
        for e in extra:
            print(f"   - {e}")
    if warn:
        print(f"Babala      : {len(warn)}")
        for w in warn:
            print(f"   ! {w}")
    if Image is None:
        print("\n(Tip: 'pip install pillow' para masuri rin ang sukat at alpha channel.)")
    if not missing and not warn:
        print("\nKumpleto at malinis ang art. Buksan ang /laro/art para makita lahat.")
    print("=" * 62)


if __name__ == "__main__":
    main()

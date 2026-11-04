import json
import re
from pathlib import Path

from src.schema import CLASS_NAMES, NON_FILL_CLASSES

DIR = Path(__file__).resolve().parent.parent / "data" / "phrasebank"
MIN_PROFILE, MIN_OPEN, MIN_UNSUP = 40, 40, 150


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


seen = {}
print(f"{'class':18}{'count':>7}  target")
for name in CLASS_NAMES:
    p = DIR / f"{name}.json"
    if not p.exists():
        print(f"{name:18}{'-':>7}  MISSING")
        continue
    phrases = json.load(open(p, encoding="utf-8"))
    target = MIN_UNSUP if name == "unsupported" else (MIN_OPEN if name == "open_text" else MIN_PROFILE)
    flag = "ok" if len(phrases) >= target else f"need {target}"
    print(f"{name:18}{len(phrases):>7}  {flag}")
    own = set()
    for ph in phrases:
        n = norm(ph)
        if n in own:
            print(f"   DUPLICATE inside {name}: {ph!r}")
        own.add(n)
        if n in seen and seen[n] != name:
            print(f"   CONFLICT: {ph!r} is in both {seen[n]} and {name}")
        seen[n] = name
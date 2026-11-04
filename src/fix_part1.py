import json
import re
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "data" / "phrasebank"

EXTRA = {
    "email": [
        "Email (for updates)", "Your email ID for registration",
        "Which email should we use to contact you?", "Gmail / Email address",
    ],
    "degree": [
        "Which degree are you currently doing?", "Degree enrolled",
        "UG degree name",
    ],
    "college": [
        "Which institute do you belong to?", "College where you are enrolled",
        "Name of your university or college",
    ],
}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


for name, extra in EXTRA.items():
    path = DIR / f"{name}.json"
    phrases = json.load(open(path, encoding="utf-8")) + extra
    seen, clean = set(), []
    for ph in phrases:
        n = norm(ph)
        if n not in seen:
            seen.add(n)
            clean.append(ph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=1, ensure_ascii=False)
    print(name, len(clean))
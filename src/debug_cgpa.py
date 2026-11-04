import json
import re
from pathlib import Path

from src import rules

path = Path(__file__).resolve().parent.parent / "data" / "resumes_synth" / "train.jsonl"
shown = 0
for line in open(path, encoding="utf-8"):
    rec = json.loads(line)
    gold = rec["gold"]["cgpa"]
    if gold is None or rules.extract_cgpa(rec["text"]) is not None:
        continue
    lines = rec["text"].splitlines()
    hit = [i for i, l in enumerate(lines) if re.search(r"(?i)cgpa|gpa|aggregate", l)]
    print(f"--- {rec['id']} | layout {rec['layout']} | gold cgpa {gold}")
    for i in hit[:2]:
        for j in range(max(0, i - 1), min(len(lines), i + 2)):
            print(("  >> " if j == i else "     ") + lines[j])
    shown += 1
    if shown == 6:
        break
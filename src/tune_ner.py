import json
import re
from pathlib import Path

from src.eval_real import same
from src.extract import extract_all

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["full_name", "college", "degree", "branch", "city", "state"]
TARGET, FLOOR = 0.98, 0.50


def words(s):
    return {w.lower() for w in re.findall(r"[A-Za-z]+", str(s))}


pairs = []
for line in open(ROOT / "data" / "resumes_synth" / "dev.jsonl", encoding="utf-8"):
    rec = json.loads(line)
    g = rec["gold"]
    profile, _, _ = extract_all(rec["text"])
    for f in FIELDS:
        gv, e = g.get(f), profile[f]
        if gv is None or e["value"] is None or e["source"] != "ner":
            continue
        if f == "full_name":
            ok = words(gv) <= words(e["value"])
        elif f == "college":
            ok = same(f, gv, e["value"]) or same(f, g["college_short"], e["value"])
        else:
            ok = same(f, gv, e["value"])
        pairs.append((e["confidence"], ok))

print(f"NER-filled values on synthetic dev: {len(pairs)}")
found = None
print(f"{'tau':>6}{'precision':>11}{'kept':>8}")
for t in [i / 100 for i in range(0, 100)]:
    kept = [ok for c, ok in pairs if c >= t]
    if not kept:
        continue
    prec = sum(kept) / len(kept)
    if t in (0.0, 0.5, 0.7, 0.9, 0.95, 0.99):
        print(f"{t:6.2f}{prec:11.3f}{len(kept) / len(pairs):8.3f}")
    if found is None and prec >= TARGET:
        found = t
final = max(found if found is not None else 0.99, FLOOR)
json.dump({"tau_ner": final, "smallest_tau_for_98pct_precision": found, "n_values": len(pairs),
           "chosen_on": "synthetic dev", "floor": FLOOR}, open(ROOT / "data" / "ner_config.json", "w"))
print(f"\nchosen tau_ner = {final} (smallest threshold with precision >= {TARGET}, floor {FLOOR})")
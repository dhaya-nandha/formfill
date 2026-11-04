import json
import re
import sys
from pathlib import Path

import pandas as pd

from src.schema import CLASS2ID, PROFILE_FIELDS, QUESTION_TYPES

FM = Path(__file__).resolve().parent.parent / "data" / "fm"
FORMS = FM / "old_forms"
PROFILE = FM / "old_profile.json"
DRAFT = FM / "test_a_draft.csv"
MISSING = object()


def n(v):
    return re.sub(r"\s+", " ", str(v).strip().lower())


def auto_label(expected, profile):
    if expected is MISSING:
        return "NEEDS_LABEL"
    if expected == "__ANY__":
        return "open_text"
    if expected is None:
        return "unsupported"
    hits = []
    for f in PROFILE_FIELDS:
        pv = profile.get(f)
        if pv is None:
            continue
        if isinstance(expected, list):
            if f == "skills" and isinstance(pv, list) and \
               all(n(x) in {n(y) for y in pv} for x in expected):
                hits.append(f)
        elif not isinstance(pv, list) and n(pv) == n(expected):
            hits.append(f)
    return hits[0] if len(hits) == 1 else "NEEDS_LABEL"


def find_conflicts(df):
    df = df.assign(_q=df["question"].map(n))
    g = df.groupby(["_q", "qtype"])["label"].nunique()
    bad = g[g > 1]
    return [(q, t) for (q, t) in bad.index]


def draft():
    profile = json.load(open(PROFILE, encoding="utf-8"))
    rows, skipped = [], []
    for path in sorted(FORMS.glob("form_*.json")):
        data = json.load(open(path, encoding="utf-8"))
        expected = data.get("expected", {})
        for q in data["questions"]:
            if q["type"] not in QUESTION_TYPES:
                skipped.append((path.name, q["question"], q["type"]))
                continue
            exp = expected.get(q["entry_id"], MISSING)
            rows.append({
                "form": path.stem,
                "question": " ".join(q["question"].split()),
                "qtype": q["type"],
                "expected": "" if exp is MISSING else json.dumps(exp, ensure_ascii=False),
                "label": auto_label(exp, profile),
            })
    df = pd.DataFrame(rows)
    df.to_csv(DRAFT, index=False, encoding="utf-8")
    print("questions kept:", len(df), "| skipped (out of scope types):", len(skipped))
    for s in skipped:
        print("  skipped:", s)
    print("\nlabel counts:")
    print(df["label"].value_counts().to_string())
    need = df[df["label"] == "NEEDS_LABEL"]
    print(f"\nNEEDS_LABEL rows to fix by hand: {len(need)}")
    for _, r in need.iterrows():
        print(f"  [{r['form']}] ({r['qtype']}) {r['question']}  -> expected {r['expected']}")
    print("\nOpen data/fm/test_a_draft.csv, fix the label column, then run:")
    print("  py -m src.build_test_a_from_forms final")


def final():
    df = pd.read_csv(DRAFT, encoding="utf-8").fillna("")
    errors = []
    for i, r in df.iterrows():
        if r["label"] not in CLASS2ID:
            errors.append(f"row {i + 2}: bad label {r['label']!r} for {r['question']!r}")
    if errors:
        print("FIX THESE FIRST:")
        for e in errors:
            print(" ", e)
        return
    conflicts = find_conflicts(df)
    if conflicts:
        print("SAME QUESTION, DIFFERENT LABELS (fix in the draft):")
        for c in conflicts:
            print(" ", c)
        return
    df = df.drop_duplicates(subset=["question", "qtype"]).reset_index(drop=True)
    out = pd.DataFrame({
        "text": [f"[{t}] {q}" for t, q in zip(df["qtype"], df["question"])],
        "question": df["question"], "qtype": df["qtype"], "label": df["label"],
        "label_id": df["label"].map(CLASS2ID), "base": df["question"],
    })
    out.to_csv(FM / "test_a.csv", index=False, encoding="utf-8")
    print("test_a rows (unique questions):", len(out))
    print(out["label"].value_counts().to_string())


if __name__ == "__main__":
    final() if len(sys.argv) > 1 and sys.argv[1] == "final" else draft()
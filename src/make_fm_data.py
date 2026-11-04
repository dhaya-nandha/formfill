import json
import random
import re
from pathlib import Path

import pandas as pd

from src.schema import CLASS_NAMES, CLASS2ID, QUESTION_TYPES

ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = ROOT / "data" / "phrasebank"
OUT = ROOT / "data" / "fm"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
TRAIN_VARIANTS = 7   # rows per train base phrase (1 clean + 6 augmented)
VAL_VARIANTS = 4     # rows per val base phrase

PREFIXES = ["Please enter your", "Enter your", "Enter", "Your"]
SUFFIXES = ["*", " *", "(required)", "as per records", ":"]

DEFAULT_W = {"short_text": 0.50, "paragraph": 0.05, "multiple_choice": 0.15,
             "dropdown": 0.20, "checkboxes": 0.10}
CHOICEY_W = {"short_text": 0.25, "paragraph": 0.05, "multiple_choice": 0.30,
             "dropdown": 0.35, "checkboxes": 0.05}
TYPE_WEIGHTS = {
    "open_text": {"short_text": 0.30, "paragraph": 0.70, "multiple_choice": 0.0,
                  "dropdown": 0.0, "checkboxes": 0.0},
    "skills": {"short_text": 0.30, "paragraph": 0.10, "multiple_choice": 0.05,
               "dropdown": 0.10, "checkboxes": 0.45},
}
for c in ["year_of_study", "branch", "degree", "state", "graduation_year", "target_role"]:
    TYPE_WEIGHTS[c] = CHOICEY_W


def pick_type(cls, rng):
    w = TYPE_WEIGHTS.get(cls, DEFAULT_W)
    return rng.choices(QUESTION_TYPES, weights=[w[t] for t in QUESTION_TYPES])[0]


def typo(q, rng):
    words = q.split(" ")
    idx = [i for i, w in enumerate(words) if len(w) >= 5 and w.isalpha()]
    if not idx:
        return q
    i = rng.choice(idx)
    w = words[i]
    j = rng.randint(1, len(w) - 3)
    words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def augment(q, rng):
    if rng.random() < 0.25 and not q.endswith("?"):
        q = rng.choice(PREFIXES) + " " + q
    if rng.random() < 0.25:
        q = q + ("" if rng.choice(SUFFIXES).startswith(" ") else " ") + rng.choice(SUFFIXES).strip()
    if rng.random() < 0.10:
        q = f"{rng.randint(1, 15)}. " + q
    r = rng.random()
    if r < 0.07:
        q = q.upper()
    elif r < 0.14:
        q = q.lower()
    elif r < 0.20:
        q = q.title()
    if rng.random() < 0.10:
        q = q.replace(" ", "  ", 1)
    if rng.random() < 0.10:
        q = q.replace("/", " / ") if "/" in q else q.replace(".", "")
    if rng.random() < 0.10:
        q = typo(q, rng)
    return re.sub(r"\s+$", "", q)


def expand(base_phrases, cls, n_variants, rng):
    rows, seen = [], set()
    for base in base_phrases:
        variants = [base]
        tries = 0
        while len(variants) < n_variants and tries < 40:
            tries += 1
            v = augment(base, rng)
            if v not in variants:
                variants.append(v)
        for v in variants:
            qtype = pick_type(cls, rng)
            key = (v, qtype)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"text": f"[{qtype}] {v}", "question": v, "qtype": qtype,
                         "label": cls, "label_id": CLASS2ID[cls], "base": base})
    return rows


def main():
    rng = random.Random(SEED)
    split = {"train": {}, "val": {}}
    for cls in CLASS_NAMES:
        phrases = json.load(open(BANK_DIR / f"{cls}.json", encoding="utf-8"))
        shuffled = phrases[:]
        rng.shuffle(shuffled)
        n_val = max(1, round(0.2 * len(shuffled)))
        split["val"][cls] = shuffled[:n_val]
        split["train"][cls] = shuffled[n_val:]

    with open(OUT / "split_base.json", "w", encoding="utf-8") as f:
        json.dump(split, f, indent=1, ensure_ascii=False)

    train_rows, val_rows = [], []
    for cls in CLASS_NAMES:
        train_rows += expand(split["train"][cls], cls, TRAIN_VARIANTS, rng)
        val_rows += expand(split["val"][cls], cls, VAL_VARIANTS, rng)

    train = pd.DataFrame(train_rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    val = pd.DataFrame(val_rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    train.to_csv(OUT / "train_raw.csv", index=False, encoding="utf-8")
    val.to_csv(OUT / "val.csv", index=False, encoding="utf-8")

    print("train_raw rows:", len(train), "| val rows:", len(val))
    share = (train["label"] == "unsupported").mean() * 100
    print(f"unsupported share of train: {share:.1f}% (limit 35%)")
    print("\nbase phrases per class (train / val):")
    for cls in CLASS_NAMES:
        print(f"  {cls:16} {len(split['train'][cls]):4} / {len(split['val'][cls]):3}")


if __name__ == "__main__":
    main()
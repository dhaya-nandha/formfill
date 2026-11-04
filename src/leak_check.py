import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FM = ROOT / "data" / "fm"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

PREFIXES = ["please enter your", "enter your", "enter", "your"]
SUFFIXES = ["as per records", "required", "mandatory"]


def norm(q):
    q = str(q).lower()
    q = re.sub(r"^\s*\d+\s*[.)]\s*", "", q)
    q = re.sub(r"[^a-z0-9]+", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def core(q):
    n = norm(q)
    for p in PREFIXES:
        if n.startswith(p + " "):
            n = n[len(p) + 1:]
            break
    for s in SUFFIXES:
        if n.endswith(" " + s):
            n = n[: -len(s) - 1]
            break
    return n


def main():
    train = pd.read_csv(FM / "train_raw.csv", encoding="utf-8")
    train["n"] = train["question"].map(norm)
    train["c"] = train["question"].map(core)

    eval_sets = {}
    for name in ["val", "test_a", "test_b"]:
        p = FM / f"{name}.csv"
        if p.exists():
            df = pd.read_csv(p, encoding="utf-8")
            df["n"] = df["question"].map(norm)
            df["c"] = df["question"].map(core)
            eval_sets[name] = df

    report = {"train_rows_before": len(train)}
    remove_core = set()
    print(f"{'set':8}{'rows':>6}{'exact':>8}{'near':>7}{'label_conflict':>16}")
    for name, df in eval_sets.items():
        exact = int(df["n"].isin(set(train["n"])).sum())
        near = int(df["c"].isin(set(train["c"])).sum())
        merged = df.merge(train[["c", "label"]].drop_duplicates(), on="c", suffixes=("", "_train"))
        conflict = int((merged["label"] != merged["label_train"]).sum())
        print(f"{name:8}{len(df):6}{exact:8}{near:7}{conflict:16}")
        report[name] = {"rows": len(df), "exact_overlap_before": exact,
                        "near_overlap_before": near, "label_conflicts": conflict}
        remove_core |= set(df["c"])

    drop = train["c"].isin(remove_core)
    report["train_rows_removed"] = int(drop.sum())
    train = train[~drop].copy()

    for name, df in eval_sets.items():
        report[name]["exact_overlap_after"] = int(df["n"].isin(set(train["n"])).sum())
        report[name]["near_overlap_after"] = int(df["c"].isin(set(train["c"])).sum())

    # conflicts inside train: same normalized text, different labels
    grp = train.groupby("n")["label"].nunique()
    report["train_internal_label_conflicts"] = int((grp > 1).sum())

    train = train.drop(columns=["n", "c"]).reset_index(drop=True)
    train.to_csv(FM / "train.csv", index=False, encoding="utf-8")
    report["train_rows_after"] = len(train)

    with open(RES / "leak_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    print(f"\ntrain rows: {report['train_rows_before']} -> {report['train_rows_after']} "
          f"(removed {report['train_rows_removed']} overlapping rows)")
    print("overlap AFTER removal:",
          {k: (v["exact_overlap_after"], v["near_overlap_after"])
           for k, v in report.items() if isinstance(v, dict)})
    print("label conflicts inside train:", report["train_internal_label_conflicts"])

    print("\nrows per class (train / val):")
    val = eval_sets.get("val")
    for cls in sorted(train["label"].unique()):
        print(f"  {cls:16} {int((train['label'] == cls).sum()):5} / "
              f"{int((val['label'] == cls).sum()) if val is not None else 0:4}")
    print(f"\nunsupported share of train: {(train['label'] == 'unsupported').mean() * 100:.1f}%")
    print("min rows in any train class:", int(train['label'].value_counts().min()))


if __name__ == "__main__":
    main()
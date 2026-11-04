import os

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # latency is measured on CPU

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES, MODELS, REAL = ROOT / "results", ROOT / "models", ROOT / "data" / "real"
FORMS = ROOT / "data" / "fm" / "old_forms"
L = []


def load(name):
    p = RES / name
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def f3(x):
    return "n/a" if x is None else f"{x:.3f}"


def dir_mb(p):
    p = Path(p)
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6 if p.exists() else None


def add(*lines):
    L.extend(lines)
    print("\n".join(lines))


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


add("# FormFill results", "",
    "All numbers come from the scripts in this repository (seed 42). "
    "SYNTHETIC = generated data, REAL = real resumes and forms.", "")

# ---- 1. field matcher ----
add("## 1. Field matcher (question -> profile field)", "")
rows = []
for name, label in [("A_tfidf", "A: TF-IDF + LogReg (baseline)"),
                    ("B_frozen", "B: frozen MiniLM + LogReg"),
                    ("C_finetuned", "C: fine-tuned MiniLM (main model)")]:
    m = load(f"fm_metrics_{name}.json")
    if m:
        s = m["sets"]
        rows.append([label] + [f3(s[k][x]) if k in s else "n/a"
                               for k in ("val", "test_a") for x in ("accuracy", "macro_f1")])
add(*table(["variant", "val acc", "val macro-F1", "test_a acc", "test_a macro-F1"], rows))
add("", "val = held-out phrasings (synthetic wording). test_a = real wording from 21 earlier forms "
    "(116 unique questions, no `branch` rows).", "")

t = load("fm_threshold.json")
if t:
    v, a = t["val_at_tau"], t.get("test_a_at_tau", {})
    add(f"Confidence threshold tau_fm = {t['tau_fm']:.2f}, chosen on val only "
        f"(target precision {t['target_precision']:.2f}).", "")
    add(*table(["set", "auto-fill precision", "coverage (of all questions)", "auto-filled"],
               [["val", pct(v["precision"]), pct(v["coverage"]), v["auto"]],
                ["test_a", pct(a.get("precision")), pct(a.get("coverage")), a.get("auto")]]))

lk = load("leak_report.json")
if lk:
    add("", "### Leakage check (train vs evaluation sets)", "")
    rows = [[k, lk[k]["rows"], f"{lk[k]['exact_overlap_before']} / {lk[k]['near_overlap_before']}",
             f"{lk[k]['exact_overlap_after']} / {lk[k]['near_overlap_after']}"]
            for k in ("val", "test_a", "test_b") if k in lk]
    add(*table(["set", "rows", "exact / near overlap before removal", "after removal"], rows))
    add("", f"Training rows {lk['train_rows_before']} -> {lk['train_rows_after']} "
        f"({lk['train_rows_removed']} removed). Label conflicts inside train: "
        f"{lk['train_internal_label_conflicts']}.")

# ---- 2. NER ----
n = load("ner_metrics.json")
if n:
    add("", "## 2. NER model (SYNTHETIC resumes only)", "")
    rows = [[typ] + [f3(n[s]["per_type"][typ]["f1-score"]) if typ in n[s]["per_type"] else "n/a"
                     for s in ("dev", "test")]
            for typ in ("NAME", "COLLEGE", "DEGREE", "BRANCH", "LOCATION", "SKILL")]
    rows.append(["overall entity F1", f3(n["dev"]["entity_f1"]), f3(n["test"]["entity_f1"])])
    add(*table(["entity", "dev F1", "test F1"], rows))

# ---- 3. real extraction ----
r2, r1 = load("real_extraction_metrics.json"), load("real_extraction_metrics_run1.json")
if r2:
    add("", "## 3. Resume extraction on REAL resumes", "")
    add(f"Scored resumes: {r2.get('n_scored', r2.get('n_resumes'))} "
        "(scanned PDFs without text are excluded, no OCR).", "")
    rows = []
    for f, v in r2["fields"].items():
        v1 = r1["fields"].get(f) if r1 else None
        rows.append([f, v["n_gold"], pct(v1["accuracy"]) if v1 else "n/a",
                     pct(v["accuracy"]), pct(v.get("rules_only_accuracy"))])
    add(*table(["field", "n (gold present)", "first run (untuned)", "after error fixes", "rules only"], rows))
    if r1:
        add("", f"Mean field accuracy: first run {f3(r1.get('mean_field_accuracy'))}, "
            f"after fixes {f3(r2.get('mean_field_accuracy'))}.")
    if "skills" in r2:
        add(f"Skills: mean recall {f3(r2['skills']['mean_recall'])}, "
            f"mean precision {f3(r2['skills']['mean_precision'])}.")
    add("", "The first run is the untuned result. The later run was tuned on the same resumes "
        "(error analysis, gold-label corrections), so it is an upper bound.")

# ---- 4. end to end ----
e, eb = load("e2e_metrics.json"), load("e2e_metrics_before_idrule.json")
if e:
    add("", "## 4. End-to-end form filling (REAL resumes x earlier forms)", "")
    add(f"{e['n_resumes']} resumes x {e['n_forms']} forms.", "")
    rows = []
    for key, label in (("extracted", "full pipeline (extracted profile)"),
                       ("gold_profile", "gold profile (matchers only)")):
        s = e[key]
        rows.append([label, s["questions"], s["fillable"], s["auto"], pct(s["precision"]),
                     pct(s["coverage_of_fillable"]), s["wrong_fills"], pct(s["review_rate"])])
    add(*table(["mode", "questions", "fillable", "AUTO", "precision", "coverage of fillable",
                "wrong fills", "REVIEW rate"], rows))
    ci = e["extracted"]
    if "precision_95ci" in ci:
        add("", f"Bootstrap 95% over resumes (full pipeline): precision {pct(ci['precision_95ci'][0])} "
            f"to {pct(ci['precision_95ci'][1])}, coverage {pct(ci['coverage_95ci'][0])} "
            f"to {pct(ci['coverage_95ci'][1])}.")
    if eb:
        add(f"Before the ID-word rule: full pipeline precision {pct(eb['extracted']['precision'])} "
            f"({eb['extracted']['wrong_fills']} wrong fills), gold profile "
            f"{pct(eb['gold_profile']['precision'])}.")
    add("", "Rule overrides (ID words, 10th/12th marks) were added after error analysis on these same forms.")

# ---- 5. efficiency ----
add("", "## 5. Efficiency (CPU only, this laptop)", "")
try:
    from transformers import AutoModelForSequenceClassification, AutoModelForTokenClassification

    from src.extract import extract_all
    from src.gform import load_form_json
    from src.pdf_text import extract_text, looks_scanned
    from src.pipeline import run_pipeline

    params = lambda m: sum(p.numel() for p in m.parameters()) / 1e6
    fm_m = AutoModelForSequenceClassification.from_pretrained(MODELS / "field_matcher")
    ner_m = AutoModelForTokenClassification.from_pretrained(MODELS / "ner")
    add(*table(["model", "size on disk (MB)", "parameters (M)"],
               [["field matcher (MiniLM)", f"{dir_mb(MODELS / 'field_matcher'):.0f}", f"{params(fm_m):.1f}"],
                ["resume NER (BERT-base)", f"{dir_mb(MODELS / 'ner'):.0f}", f"{params(ner_m):.1f}"]]))
    pdf = next(p for p in sorted(REAL.glob("*.pdf"))
               if (p.parent / (p.stem + ".gold.json")).exists() and not looks_scanned(extract_text(p)))
    t0 = time.time()
    for _ in range(3):
        text = extract_text(pdf)
    t_pdf = (time.time() - t0) / 3
    profile, _, _ = extract_all(text)
    t0 = time.time()
    for _ in range(5):
        profile, _, _ = extract_all(text)
    t_res = (time.time() - t0) / 5
    forms = [load_form_json(p) for p in sorted(FORMS.glob("form_*.json"))]
    run_pipeline(profile, forms[0]["questions"])
    t0 = time.time()
    for f in forms:
        run_pipeline(profile, f["questions"])
    t_form = (time.time() - t0) / len(forms)
    add("", f"Per resume: PDF text {t_pdf:.2f} s + NER and rules {t_res:.2f} s. "
        f"Per form ({len(forms)} forms, about {sum(len(f['questions']) for f in forms) / len(forms):.0f} questions): "
        f"{t_form:.2f} s.")
except Exception as ex:
    add(f"(efficiency section failed: {ex})")

add("", "## Figures in results/", "")
add(*[f"- {p.name}" for p in sorted(RES.glob("*.png"))])
(RES / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
print("\nSaved results/SUMMARY.md")
import csv
import json
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.eval_real import flat, gold_value, same
from src.extract import extract_all
from src.gform import load_form_json
from src.option_matcher import parse_year
from src.pdf_text import extract_text, looks_scanned
from src.pipeline import run_pipeline, user_entry
from src.schema import PROFILE_FIELDS

ROOT = Path(__file__).resolve().parent.parent
REAL, RES = ROOT / "data" / "real", ROOT / "results"
FORMS = ROOT / "data" / "fm" / "old_forms"
DRAFT = ROOT / "data" / "fm" / "test_a_draft.csv"
PRIVATE = {"full_name", "email", "phone", "github", "linkedin"}


def qkey(form, q, t):
    return (form, " ".join(str(q).split()).lower(), t)


def answer_ok(field, gold, answer):
    ans = answer if isinstance(answer, list) else [answer]
    if field == "skills":
        gs = {flat(s) for s in gold}
        items = [x.strip() for a in ans for x in str(a).split(",") if x.strip()]
        return bool(items) and all(flat(i) in gs for i in items)
    a = str(ans[0])
    if field == "year_of_study":
        return parse_year(gold) is not None and parse_year(gold) == parse_year(a)
    if field == "graduation_year":
        ys = re.findall(r"(?:19|20)\d{2}", a)
        return bool(ys) and ys[-1] == str(gold).strip()
    if field == "target_role":
        return flat(gold) == flat(a)
    return same(field, gold, a)


def gold_profile(gold):
    p = {}
    for f in PROFILE_FIELDS:
        v = gold_value(gold, f)
        p[f] = {"value": v, "confidence": 1.0 if v is not None else 0.0,
                "source": "user" if v is not None else "none", "raw": None}
    return p


def user_fields(gold):
    out = {}
    for f in ("year_of_study", "target_role"):
        v = gold_value(gold, f)
        if isinstance(v, list):
            v = v[0] if v else None
        if v is not None:
            out[f] = user_entry(str(v))
    return out


def evaluate(profiles, golds, forms, labels):
    cases, skipped = [], 0
    for tag, prof in profiles.items():
        gold = golds[tag]
        for fname, form in forms.items():
            rows = run_pipeline(prof, form["questions"])
            for q, r in zip(form["questions"], rows):
                lab = labels.get(qkey(fname, q["question"], q["type"]))
                if lab is None:
                    skipped += 1
                    continue
                gv = gold_value(gold, lab) if lab in PROFILE_FIELDS else None
                expected_fill = gv is not None
                if r["status"] == "AUTO":
                    ok = expected_fill and answer_ok(lab, gv, r["answer"])
                    outcome = "correct_fill" if ok else "wrong_fill"
                else:
                    outcome = "missed" if expected_fill else "correct_review"
                cases.append({"resume": tag, "form": fname, "question": q["question"],
                              "type": q["type"], "gold_class": lab, "pred_field": r["predicted_field"],
                              "status": r["status"], "answer": r["answer"], "outcome": outcome,
                              "fillable": expected_fill, "reason": r["reason"]})
    return cases, skipped


def summarize(cases):
    c = Counter(x["outcome"] for x in cases)
    auto = c["correct_fill"] + c["wrong_fill"]
    fillable = sum(x["fillable"] for x in cases)
    auto_on_fill = sum(1 for x in cases if x["fillable"] and x["status"] == "AUTO")
    wrong_unexpected = sum(1 for x in cases if x["outcome"] == "wrong_fill" and not x["fillable"])
    s = {"questions": len(cases), "fillable": fillable, "auto": auto,
         "correct_fills": c["correct_fill"], "wrong_fills": c["wrong_fill"],
         "wrong_fills_where_review_expected": wrong_unexpected,
         "wrong_fills_bad_value_or_field": c["wrong_fill"] - wrong_unexpected,
         "review": len(cases) - auto,
         "precision": c["correct_fill"] / auto if auto else None,
         "coverage_of_fillable": auto_on_fill / fillable if fillable else None,
         "correct_coverage": c["correct_fill"] / fillable if fillable else None,
         "review_rate": (len(cases) - auto) / len(cases) if cases else None}
    per = defaultdict(lambda: {"n": 0, "auto": 0, "correct": 0})
    for x in cases:
        if x["fillable"]:
            p = per[x["gold_class"]]
            p["n"] += 1
            p["auto"] += x["status"] == "AUTO"
            p["correct"] += x["outcome"] == "correct_fill"
    s["per_field"] = dict(per)
    return s


def bootstrap(cases, n=1000, seed=42):
    by = defaultdict(lambda: [0, 0, 0, 0])
    for x in cases:
        b = by[x["resume"]]
        b[0] += x["outcome"] == "correct_fill"
        b[1] += x["status"] == "AUTO"
        b[2] += x["fillable"]
        b[3] += x["fillable"] and x["status"] == "AUTO"
    tags, rng, prec, cov = list(by), random.Random(seed), [], []
    for _ in range(n):
        s = [by[rng.choice(tags)] for _ in tags]
        a, ok = sum(v[1] for v in s), sum(v[0] for v in s)
        f, af = sum(v[2] for v in s), sum(v[3] for v in s)
        if a and f:
            prec.append(ok / a)
            cov.append(af / f)
    q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
    return {"precision_95ci": [q(prec, 0.025), q(prec, 0.975)],
            "coverage_95ci": [q(cov, 0.025), q(cov, 0.975)]}


def pct(x):
    return "  n/a" if x is None else f"{x * 100:5.1f}%"


def show(name, s):
    print(f"\n=== {name} ===")
    print(f"questions {s['questions']} | fillable {s['fillable']} | AUTO {s['auto']} | REVIEW {s['review']}")
    print(f"auto-fill precision {pct(s['precision'])} | coverage of fillable {pct(s['coverage_of_fillable'])}"
          f" | correct coverage {pct(s['correct_coverage'])} | REVIEW rate {pct(s['review_rate'])}")
    print(f"wrong fills {s['wrong_fills']} (where REVIEW was expected: {s['wrong_fills_where_review_expected']},"
          f" bad value or field: {s['wrong_fills_bad_value_or_field']})")
    print(f"  {'field':16}{'fillable':>9}{'AUTO':>6}{'correct':>9}")
    for f, p in sorted(s["per_field"].items()):
        print(f"  {f:16}{p['n']:9}{p['auto']:6}{p['correct']:9}")


def main():
    t0 = time.time()
    labels = {}
    for r in csv.DictReader(open(DRAFT, encoding="utf-8")):
        labels[qkey(r["form"], r["question"], r["qtype"])] = r["label"]
    forms = {p.stem: load_form_json(p) for p in sorted(FORMS.glob("form_*.json"))}
    golds, ext_profiles, gold_profiles, scanned = {}, {}, {}, []
    n = 0
    for pdf in sorted(REAL.glob("*.pdf")):
        gp = pdf.parent / (pdf.stem + ".gold.json")
        if not gp.exists():
            continue
        n += 1
        tag = f"#{n:02d}"
        gold = json.load(open(gp, encoding="utf-8"))
        text = extract_text(pdf)
        if looks_scanned(text):
            scanned.append(tag)
            continue
        golds[tag] = gold
        prof, _, _ = extract_all(text)
        prof.update(user_fields(gold))
        ext_profiles[tag] = prof
        gprof = gold_profile(gold)
        gprof.update(user_fields(gold))
        gold_profiles[tag] = gprof
    print(f"resumes scored: {len(golds)} | scanned excluded: {scanned} | forms: {len(forms)}")

    out = {"n_resumes": len(golds), "n_forms": len(forms)}
    for name, profs in (("MODE 1: extracted profile (full pipeline)", ext_profiles),
                        ("MODE 2: gold profile (field matcher + option matcher only)", gold_profiles)):
        cases, skipped = evaluate(profs, golds, forms, labels)
        s = summarize(cases)
        s["skipped_unlabelled_questions"] = skipped
        if name.startswith("MODE 1"):
            s.update(bootstrap(cases))
        show(name, s)
        if "precision_95ci" in s:
            print(f"bootstrap 95% over resumes: precision {pct(s['precision_95ci'][0])} to {pct(s['precision_95ci'][1])},"
                  f" coverage {pct(s['coverage_95ci'][0])} to {pct(s['coverage_95ci'][1])}")
        print(f"(questions without a label, skipped: {skipped})")
        key = "extracted" if name.startswith("MODE 1") else "gold_profile"
        out[key] = s
        if key == "extracted":
            bad = [x for x in cases if x["outcome"] == "wrong_fill"]
            print(f"\n--- first {min(25, len(bad))} wrong fills of {len(bad)} (private values hidden) ---")
            for x in bad[:25]:
                hide = x["gold_class"] in PRIVATE or x["pred_field"] in PRIVATE
                ans = "<hidden>" if hide else x["answer"]
                print(f"  {x['resume']} {x['form']} [{x['type']}] {x['question'][:34]!r}: gold class "
                      f"{x['gold_class']}, predicted {x['pred_field']}, answer {ans}")
            with open(REAL / "e2e_details.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(cases[0]))
                w.writeheader()
                w.writerows(cases)
    with open(RES / "e2e_metrics.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nSaved results/e2e_metrics.json (numbers only) and data/real/e2e_details.csv (private) | {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
import csv
import json
import re
import time
from pathlib import Path

from src import rules
from src.extract import extract_all
from src.pdf_text import extract_text, looks_scanned
from src.schema import PROFILE_FIELDS

ROOT = Path(__file__).resolve().parent.parent
REAL, RES = ROOT / "data" / "real", ROOT / "results"
RES.mkdir(exist_ok=True)
EVAL = [f for f in PROFILE_FIELDS if f not in ("year_of_study", "target_role")]
PRIVATE = {"full_name", "email", "phone", "github", "linkedin"}


def flat(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def link(s):
    s = re.sub(r"^https?://", "", str(s).lower().strip().rstrip("/"))
    return re.sub(r"^www\.", "", s)


def college_core(s):
    return re.sub(r"\(.*?\)", " ", str(s)).split(",")[0]


def acronym(s):
    words = [w for w in re.findall(r"[A-Za-z]+", college_core(s))
             if w.lower() not in ("of", "and", "the", "for")]
    return "".join(w[0] for w in words).upper()


def same(field, g, p):
    if field == "phone":
        return re.sub(r"\D", "", str(g))[-10:] == re.sub(r"\D", "", str(p))[-10:]
    if field == "cgpa":
        try:
            return abs(float(g) - float(p)) < 0.005
        except ValueError:
            return False
    if field == "graduation_year":
        return str(g).strip() == str(p).strip()
    if field in ("github", "linkedin"):
        return link(g) == link(p)
    if field == "email":
        return str(g).strip().lower() == str(p).strip().lower()
    if field == "degree":
        return (rules.normalize_degree(str(g)) or flat(g)) == (rules.normalize_degree(str(p)) or flat(p))
    if field == "branch":
        return (rules.normalize_branch(str(g)) or flat(g)) == (rules.normalize_branch(str(p)) or flat(p))
    if field == "college":
        a, b = flat(college_core(g)), flat(college_core(p))
        short, long_ = sorted([a, b], key=len)
        if a == b or (len(short) >= 6 and short in long_):
            return True
        return (len(flat(p)) >= 3 and acronym(g) == flat(p).upper()) or \
               (len(flat(g)) >= 3 and acronym(p) == flat(g).upper())
    return flat(g) == flat(p)


def gold_value(gold, field):
    v = gold.get(field)
    return None if v in (None, "", []) else v

def written(g, text):
    t = flat(text)
    return all(flat(w) in t for w in re.findall(r"[A-Za-z0-9]+", str(g)))


def empty_stats():
    return {f: {"n_gold": 0, "filled": 0, "correct": 0, "extra": 0} for f in EVAL}


def score(stats, field, g, p):
    st = stats[field]
    if g is not None:
        st["n_gold"] += 1
        if p is not None:
            st["filled"] += 1
            st["correct"] += bool(same(field, g, p))
    elif p is not None:
        st["extra"] += 1




def main():
    full, rl = empty_stats(), empty_stats()
    sk_recall, sk_prec, details, missing, errors = [], [], [], [], []
    scanned, not_in_text = [], {"city": 0, "state": 0, "graduation_year": 0}
    n = scored = 0
    t0 = time.time()
    for pdf in sorted(REAL.glob("*.pdf")):
        gp = pdf.parent / (pdf.stem + ".gold.json")
        if not gp.exists():
            missing.append(pdf.name)
            continue
        n += 1
        tag = f"#{n:02d}"
        gold = json.load(open(gp, encoding="utf-8"))
        text = extract_text(pdf)
        if looks_scanned(text):
            scanned.append(tag)
            continue
        scored += 1
        profile, _, trunc = extract_all(text)
        ruled = rules.extract_rule_fields(text)
        for f in EVAL:
            if f == "skills":
                continue
            g, p = gold_value(gold, f), profile[f]["value"]
            if f in ("city", "state", "graduation_year") and g is not None and not written(g, text):
                not_in_text[f] += 1
                continue
            score(full, f, g, p)
            score(rl, f, g, ruled.get(f))
            if g is not None and (p is None or not same(f, g, p)):
                status = "MISSING" if p is None else "WRONG"
                show = status if f in PRIVATE else f"{status}: gold={g!r} got={p!r}"
                errors.append(f"{tag} {f}: {show}")
            elif g is None and p is not None:
                errors.append(f"{tag} {f}: EXTRA" + ("" if f in PRIVATE else f" got={p!r}"))
            details.append({"resume": tag, "file": pdf.name, "field": f, "gold": g, "pred": p,
                            "conf": profile[f]["confidence"], "source": profile[f]["source"]})
        gs = [flat(s) for s in (gold.get("skills") or [])]
        ps = [flat(s) for s in (profile["skills"]["value"] or [])]
        if gs:
            sk_recall.append(sum(s in ps for s in gs) / len(gs))
            sk_prec.append(sum(s in gs for s in ps) / len(ps) if ps else 0.0)

    if missing:
        print("PDFs WITHOUT a gold file (skipped):", missing)
    print(f"\nresumes with gold: {n} | scored: {scored} | time {time.time() - t0:.1f}s")
    print(f"scanned / no-text PDFs (excluded, no OCR): {scanned}")
    print(f"gold city/state not written in the resume (excluded): {not_in_text}\n")
    print(f"{'field':16}{'n_gold':>7}{'accuracy':>10}{'filled':>8}{'precision':>10}{'extra':>7}{'rules-only acc':>16}")
    out = {"n_with_gold": n, "n_scored": scored, "scanned_excluded": len(scanned),
           "city_state_not_in_text_excluded": not_in_text, "fields": {}}
    accs = []
    for f in EVAL:
        if f == "skills":
            continue
        a, r = full[f], rl[f]
        acc = a["correct"] / a["n_gold"] if a["n_gold"] else None
        prec = a["correct"] / a["filled"] if a["filled"] else None
        racc = r["correct"] / r["n_gold"] if r["n_gold"] else None
        fmt = lambda x: "   n/a" if x is None else f"{x:6.3f}"
        print(f"{f:16}{a['n_gold']:7}{fmt(acc):>10}{a['filled']:8}{fmt(prec):>10}{a['extra']:7}{fmt(racc):>16}")
        out["fields"][f] = {**a, "accuracy": acc, "precision": prec, "rules_only_accuracy": racc}
        if acc is not None:
            accs.append(acc)
    if sk_recall:
        mr, mp = sum(sk_recall) / len(sk_recall), sum(sk_prec) / len(sk_prec)
        print(f"{'skills':16}{len(sk_recall):7}  mean recall {mr:.3f} | mean precision {mp:.3f}")
        out["skills"] = {"n": len(sk_recall), "mean_recall": mr, "mean_precision": mp}
    if accs:
        print(f"\nmean accuracy over {len(accs)} non-skill fields: {sum(accs) / len(accs):.3f}")
        out["mean_field_accuracy"] = sum(accs) / len(accs)
    print("\n--- errors (gold values hidden for name/email/phone/links) ---")
    for e in errors:
        print(" ", e)
    with open(RES / "real_extraction_metrics.json", "w") as f:
        json.dump(out, f, indent=1)
    with open(REAL / "eval_details.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["resume", "file", "field", "gold", "pred", "conf", "source"])
        w.writeheader()
        w.writerows(details)
    print("\nSaved results/real_extraction_metrics.json (numbers only) and data/real/eval_details.csv (private)")


if __name__ == "__main__":
    main()
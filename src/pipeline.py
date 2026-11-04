import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.option_matcher import match_checkboxes, match_option, parse_year
from src.schema import CLASS_NAMES, QUESTION_TYPES

ROOT = Path(__file__).resolve().parent.parent
FM_DIR = ROOT / "models" / "field_matcher"
NER_CFG = ROOT / "data" / "ner_config.json"
CHOICE = {"multiple_choice", "dropdown", "checkboxes"}
_fm = {}

import re as _re

_ID_WORDS = _re.compile(
    r"(?i)\b(pan|aadhaar|aadhar|passport|voter|roll|registration|enrol+ment|account|upi|ifsc|"
    r"bank|pin\s*code|pincode|zip|hall\s*ticket|employee|student\s*id|college\s*id)\b")
_SCHOOL_CS = _re.compile(r"(?<![A-Za-z])(?:X|XI|XII)(?![A-Za-z])")
_SCHOOL_CI = _re.compile(
    r"(?i)(?<![A-Za-z])(?:10th|12th|tenth|twelfth|ssc|hsc|cbse|icse|intermediate|secondary|"
    r"matriculation|schooling|school|diploma|class\s*(?:x|xii|10|12)|std\s*(?:x|xii|10|12))(?![A-Za-z])")


def id_override(question, field):
    """ID questions and school (10th/12th) questions are never filled from the profile."""
    if field in ("phone", "email", "full_name", "college", "graduation_year", "cgpa") \
            and _ID_WORDS.search(question):
        return "unsupported"
    if field in ("cgpa", "graduation_year", "college", "degree", "branch") \
            and (_SCHOOL_CS.search(question) or _SCHOOL_CI.search(question)):
        return "unsupported"
    return field


def load_fm():
    if not _fm:
        tok = AutoTokenizer.from_pretrained(FM_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(FM_DIR)
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        cfg = json.load(open(FM_DIR / "fm_config.json"))
        _fm.update(tok=tok, model=model.to(dev).eval(), dev=dev, tau=float(cfg["tau_fm"]))
    return _fm


def load_tau_ner():
    try:
        return float(json.load(open(NER_CFG))["tau_ner"])
    except Exception:
        return 0.5


def predict_fields(questions):
    fm = load_fm()
    texts = [f"[{q['type']}] {' '.join(q['question'].split())}" for q in questions]
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            enc = fm["tok"](texts[i:i + 64], truncation=True, max_length=48,
                            padding=True, return_tensors="pt")
            enc = {k: v.to(fm["dev"]) for k, v in enc.items()}
            probs = torch.softmax(fm["model"](**enc).logits.float(), dim=-1).cpu()
            conf, idx = probs.max(-1)
            out += [(CLASS_NAMES[int(j)], float(c)) for c, j in zip(conf, idx)]
    return out


def _year_text(v):
    n = parse_year(v)
    return {1: "1st Year", 2: "2nd Year", 3: "3rd Year", 4: "4th Year"}.get(n, str(v))


def text_answer(field, entry):
    v = entry["value"]
    if field == "skills":
        return ", ".join(v)
    if field == "branch" and entry.get("raw"):
        return entry["raw"]
    if field == "year_of_study":
        return _year_text(v)
    return str(v)


def user_entry(value):
    return {"value": value, "confidence": 1.0, "source": "user", "raw": None}


def run_pipeline(profile, questions, tau_fm=None, tau_ner=None):
    fm_tau = load_fm()["tau"] if tau_fm is None else tau_fm
    ner_tau = load_tau_ner() if tau_ner is None else tau_ner
    supported = [q for q in questions if q["type"] in QUESTION_TYPES]
    preds = iter(predict_fields(supported) if supported else [])
    rows = []
    for q in questions:
        row = {"entry_id": q["entry_id"], "question": q["question"], "type": q["type"],
               "predicted_field": None, "confidence": 0.0, "answer": None,
               "status": "REVIEW", "reason": ""}
        rows.append(row)
        if q["type"] not in QUESTION_TYPES:
            row["reason"] = f"question type '{q['type']}' is not supported"
            continue
        field, conf = next(preds)
        field = id_override(q["question"], field)
        row["predicted_field"], row["confidence"] = field, conf
        if field == "open_text":
            row["reason"] = "write this yourself"
            continue
        if field == "unsupported":
            row["reason"] = "not in profile"
            continue
        if conf < fm_tau:
            row["reason"] = f"unsure what this asks (maybe {field})"
            continue
        entry = profile.get(field) or {}
        v = entry.get("value")
        if v in (None, "", []):
            row["reason"] = "missing in profile"
            continue
        if entry.get("source") == "ner" and entry.get("confidence", 0) < ner_tau:
            row["reason"] = "low confidence in profile value"
            continue
        if q["type"] in CHOICE:
            if field == "skills":
                if q["type"] == "checkboxes":
                    r = match_checkboxes(v, q["options"])
                    if r["options"]:
                        row["answer"], row["status"] = r["options"], "AUTO"
                    else:
                        row["reason"] = r["reason"]
                else:
                    row["reason"] = "choose your skills from the list yourself"
                continue
            r = match_option(field, v, q["options"])
            if r["option"]:
                row["answer"] = [r["option"]] if q["type"] == "checkboxes" else r["option"]
                row["status"] = "AUTO"
            else:
                row["reason"] = r["reason"]
        else:
            row["answer"], row["status"] = text_answer(field, entry), "AUTO"
    return rows


def show(rows):
    print(f"{'status':7}{'field (conf)':26}{'type':16}{'question':42}answer / reason")
    for r in rows:
        f = f"{r['predicted_field']} ({r['confidence']:.2f})" if r["predicted_field"] else "-"
        a = r["answer"] if r["status"] == "AUTO" else r["reason"]
        a = ", ".join(a) if isinstance(a, list) else str(a)
        print(f"{r['status']:7}{f:26}{r['type']:16}{r['question'][:40]:42}{a[:38]}")
    n_auto = sum(r["status"] == "AUTO" for r in rows)
    print(f"\nAUTO {n_auto} | REVIEW {len(rows) - n_auto} | total {len(rows)}")


def main():
    from src.extract import extract_all
    from src.gform import build_prefill_link, load_form_json, parse_form
    from src.pdf_text import extract_text

    ap = argparse.ArgumentParser()
    ap.add_argument("resume")
    ap.add_argument("form", help="Google Form link or a form_xx.json file")
    ap.add_argument("--year", help="your current year of study, e.g. 3")
    ap.add_argument("--role", help="role you apply for, e.g. 'AI Engineer'")
    a = ap.parse_args()

    profile, _, _ = extract_all(extract_text(a.resume))
    if a.year:
        profile["year_of_study"] = user_entry(a.year)
    if a.role:
        profile["target_role"] = user_entry(a.role)
    form = load_form_json(a.form) if a.form.lower().endswith(".json") else parse_form(a.form)
    print(f"form: {form.get('name') or '(no title)'} | questions: {len(form['questions'])}\n")
    rows = run_pipeline(profile, form["questions"])
    show(rows)
    if form.get("url"):
        answers = {r["entry_id"]: r["answer"] for r in rows if r["status"] == "AUTO"}
        print("\npre-filled link:\n" + build_prefill_link(form["url"], answers))


if __name__ == "__main__":
    main()
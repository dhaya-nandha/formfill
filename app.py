import hashlib
import json

import pandas as pd
import streamlit as st

from src.extract import extract_all
from src.gform import (FormError, SignInRequired, build_prefill_link, parse_form,
                       parse_form_browser)
from src.pdf_text import extract_text, looks_scanned
from src.pipeline import load_fm, load_tau_ner, run_pipeline, user_entry
from src.schema import PROFILE_FIELDS, QUESTION_TYPES

st.set_page_config(page_title="FormFill", layout="wide")

EDIT_FIELDS = [f for f in PROFILE_FIELDS if f not in ("year_of_study", "target_role")]
YEARS = ["", "1st Year", "2nd Year", "3rd Year", "4th Year"]
SEP = " | "


def cell(x):
    return "" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x).strip()


def show_value(v):
    if v is None:
        return ""
    return ", ".join(v) if isinstance(v, list) else str(v)


def empty_entry():
    return {"value": None, "confidence": 0.0, "source": "none", "raw": None}


def profile_rows(profile):
    return pd.DataFrame([{"field": f, "value": show_value(profile[f]["value"]),
                          "confidence": round(profile[f]["confidence"], 2),
                          "source": profile[f]["source"]} for f in EDIT_FIELDS])


def rebuild_profile(df, original, year, role):
    out = {}
    for _, r in df.iterrows():
        f, new = r["field"], cell(r["value"])
        orig = original[f]
        if new == show_value(orig["value"]).strip():
            out[f] = orig
        elif new == "":
            out[f] = empty_entry()
        else:
            val = [s.strip() for s in new.split(",") if s.strip()] if f == "skills" else new
            out[f] = user_entry(val)
    out["year_of_study"] = user_entry(year) if year else empty_entry()
    out["target_role"] = user_entry(role.strip()) if role.strip() else empty_entry()
    return out


def check(q, ans):
    """Returns (value for the link or None, problem or None)."""
    ans = cell(ans)
    if not ans:
        return None, None
    if q["type"] in ("dropdown", "multiple_choice"):
        return (ans, None) if ans in q["options"] else (None, "not one of the options")
    if q["type"] == "checkboxes":
        parts = [p.strip() for p in ans.split("|") if p.strip()]
        if parts and all(p in q["options"] for p in parts):
            return parts, None
        return None, "not all of these are options (separate options with ' | ')"
    return ans, None


def parse_manual(text):
    qs = []
    for i, line in enumerate([l for l in text.splitlines() if l.strip()], 1):
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) < 2 or parts[0] not in QUESTION_TYPES:
            return None, f"line {i}: use  type | question | option1 ; option2"
        opts = [o.strip() for o in parts[2].split(";") if o.strip()] if len(parts) == 3 else []
        qs.append({"entry_id": f"manual.{i}", "question": parts[1], "type": parts[0],
                   "options": opts, "required": False})
    return qs, None


n = st.session_state.get("clear_n", 0)

with st.sidebar:
    st.subheader("About")
    st.write("Two models trained for this project (a resume NER model and a question "
             "matcher) plus simple rules. When it is unsure, it asks you instead of guessing.")
    fm = load_fm()
    st.caption(f"Question threshold {fm['tau']:.2f} | profile threshold {load_tau_ner():.2f}")
    st.caption("Your resume is processed on this computer and nothing is saved to disk.")
    if st.button("Clear my data"):
        st.session_state.clear()
        st.session_state["clear_n"] = n + 1
        st.rerun()

st.title("FormFill")
st.caption("Fills Google Form applications from your resume. You always review the form and click Submit yourself.")

# ---------------- Step 1 ----------------
st.header("1. Your profile")
c1, c2 = st.columns(2)
up = c1.file_uploader("Resume PDF (text-based)", type=["pdf"], key=f"resume_{n}")
pasted = c2.text_area("...or paste the resume text", height=140, key=f"paste_{n}")
if st.button("Extract profile", type="primary"):
    text = ""
    if up is not None:
        text = extract_text(up.getvalue())
        if looks_scanned(text):
            st.warning("This PDF has almost no text (scanned?). Scanned PDFs are not supported. "
                       "Paste the text instead.")
            text = pasted
    else:
        text = pasted
    if not text.strip():
        st.error("Upload a text-based PDF or paste the resume text.")
    else:
        with st.spinner("Reading your resume..."):
            profile, _, _ = extract_all(text)
        st.session_state["orig_profile"] = profile
        st.session_state["profile_ver"] = st.session_state.get("profile_ver", 0) + 1

profile = None
if "orig_profile" in st.session_state:
    orig = st.session_state["orig_profile"]
    ver = st.session_state["profile_ver"]
    st.caption("Fix any wrong value in the table. An empty value means 'not found'. "
               "Skills are separated by commas.")
    edited_profile = st.data_editor(profile_rows(orig), key=f"prof_{ver}", hide_index=True,
                                    disabled=["field", "confidence", "source"])
    d1, d2 = st.columns(2)
    year = d1.selectbox("Your current year of study", YEARS, key="year")
    role = d2.text_input("Role you are applying for", key="role")
    profile = rebuild_profile(edited_profile, orig, year, role)
else:
    st.info("Upload your resume and press 'Extract profile'.")

# ---------------- Step 2 ----------------
st.header("2. Google Form")
url = st.text_input("Form link (the form must open without Google sign-in)", key="form_url")
if st.button("Read form"):
    form, err = None, None
    try:
        with st.spinner("Reading the form..."):
            form = parse_form(url.strip())
    except SignInRequired as e:
        err = str(e)
    except FormError as first:
        try:
            with st.spinner("Trying the browser fallback..."):
                form = parse_form_browser(url.strip())
        except FormError as second:
            err = f"{first}. {second}"
    if err:
        st.error(err)
    if form:
        st.session_state["form"] = form

with st.expander("Form link not working? Paste the questions manually (no pre-filled link in this mode)"):
    manual = st.text_area("One per line:  type | question | option1 ; option2\n"
                          "types: short_text, paragraph, multiple_choice, dropdown, checkboxes",
                          key=f"manual_{n}", height=120)
    if st.button("Use these questions"):
        qs, err = parse_manual(manual)
        if err:
            st.error(err)
        else:
            st.session_state["form"] = {"name": "(manual)", "questions": qs, "url": None}

form = st.session_state.get("form")
if form is None:
    st.info("Paste a form link and press 'Read form'.")
elif profile is None:
    st.info("Extract your profile first (step 1).")
else:
    st.success(f"Form: {form.get('name') or '(no title)'} | {len(form['questions'])} questions")
    with st.spinner("Matching questions to your profile..."):
        rows = run_pipeline(profile, form["questions"])
    sig = hashlib.md5(json.dumps([{f: profile[f]["value"] for f in profile},
                                  form.get("url"), len(rows)],
                                 default=str, sort_keys=True).encode()).hexdigest()[:10]
    df = pd.DataFrame([{
        "status": "AUTO" if r["status"] == "AUTO" else "REVIEW",
        "question": r["question"], "type": r["type"],
        "field": r["predicted_field"] or "-", "conf": round(r["confidence"], 2),
        "answer": (SEP.join(r["answer"]) if isinstance(r["answer"], list) else (r["answer"] or "")),
        "why": r["reason"],
        "options": SEP.join(q["options"])[:200],
    } for r, q in zip(rows, form["questions"])])
    n_auto = int((df["status"] == "AUTO").sum())
    st.write(f"**AUTO {n_auto}** (filled for you) | **REVIEW {len(df) - n_auto}** (check or type the answer yourself)")
    st.caption("Only the 'answer' column can be edited. For dropdown and multiple-choice questions the "
               "answer must match an option exactly; for checkboxes separate options with ' | '.")
    edited = st.data_editor(df, key=f"map_{sig}", hide_index=True, num_rows="fixed",
                            disabled=[c for c in df.columns if c != "answer"])

    # ---------------- Step 3 ----------------
    st.header("3. Fill")
    answers, problems = {}, []
    for i, q in enumerate(form["questions"]):
        val, prob = check(q, edited.iloc[i]["answer"])
        if prob:
            problems.append(f"Row {i + 1} ({q['question'][:40]}): {prob}, so it is left out.")
        elif val is not None:
            answers[q["entry_id"]] = val
    for p in problems:
        st.warning(p)
    left = [q["question"] for q in form["questions"] if q["entry_id"] not in answers]
    if form.get("url"):
        if st.button("Generate pre-filled link", type="primary"):
            st.session_state["link"] = build_prefill_link(form["url"], answers)
        if st.session_state.get("link"):
            st.code(st.session_state["link"], language=None)
            st.link_button("Open the pre-filled form", st.session_state["link"])
            st.caption("This link contains your answers. Check every field in the form, then submit it yourself.")
    else:
        st.info("Manual mode: copy the answers from the table above into your form.")
    if left:
        st.caption(f"{len(left)} question(s) have no answer yet: " + "; ".join(q[:30] for q in left[:6]))
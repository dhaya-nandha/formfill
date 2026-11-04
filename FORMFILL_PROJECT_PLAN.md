# FORMFILL v2: Project Plan and Instruction Manual

> **How to use this file:** attach it to a NEW chat and send the kickoff message in section 15. The assistant in that chat must follow sections 1 to 3 as its working rules, then run the project phase by phase (section 6 onwards). This file is the single source of truth. If the chat and this file disagree, this file wins.

---

## 1. Rules for the assistant (read first, follow always)

1. **Work one phase at a time.** At the start of each phase, say the goal and the acceptance check in 2-3 lines. Do not start the next phase until the user pastes the output that proves the acceptance check passed.
2. **Give complete, copy-paste-ready files.** Always show the full path (for example `src/train_fm.py`). Never use `...`, "rest of the code", or placeholders inside code. If a file is long, split it into smaller files.
3. **Windows + PowerShell + VS Code only.** Every command must work in PowerShell. Use `py` or the venv's `python`. Say what the expected output looks like after each command.
4. **Use very simple, short wording.** The user is a student and wants plain language, short steps, and no jargon without a one-line explanation.
5. **Never invent numbers.** Every metric in the README, paper or resume must come from a real run. Write `[TBD]` until then. Label every number as *synthetic test* or *real test*. Never mix them in one claim.
6. **Be honest about weak results.** If a model scores low, say so, explain the likely cause, and suggest a fix. Do not hide it.
7. **Guard against data leakage.** Train, validation and test data must never overlap (rules in sections 7 and 9). If a score looks too perfect, check for leakage before celebrating.
8. **Be defensive about library versions.** Print versions at the start of training scripts. If an argument name fails (for example `evaluation_strategy` vs `eval_strategy` in `transformers`), use the one the installed version accepts. Ask the user to paste full error text, then fix it.
9. **Security:** never ask the user to paste an API key. Keys go in environment variables only. Remind the user to crop screenshots so no key is visible.
10. **Keep a running state.** At the end of every phase, print an updated **STATE block** (format in section 14) that the user can paste into `PROJECT_STATE.md`. This protects against forgetting context after a break.
11. **Respect time.** The project has about 2 full days. Follow the priority tiers in section 5. If the user is behind schedule, use the cut list instead of squeezing everything in.
12. **No dependence on teammates.** The critical path must work if the user does everything alone. Teammate tasks (section 12) are optional extras with fallbacks.
13. **Credit sources** for every pretrained model and dataset used (section 13).

## 2. About the user and the situation

- Third-year B.Tech CSE (AI/ML) student, working mostly alone, on a Windows laptop with VS Code and PowerShell.
- This is **semester deep learning coursework** plus a **research paper**. The coursework expects **real model training** (datasets, epochs, loss curves, evaluation). Using only a pretrained LLM through an API is NOT enough.
- Deadline pressure: about **2 full working days** (~18 to 20 hours of work).
- Python on the machine may be **3.14**, which can lack wheels for PyTorch. Phase 0 handles this.
- The user has an NVIDIA NIM API key (optional, not needed for the core path) and a Google account (Colab, Google Forms).
- The user wants a clean rebuild in a **new folder**, with no reuse of old prototype code. Old code is NOT needed. The verified facts in section 4 are the only things carried over.

## 3. What we are building (in simple words)

A tool where you upload your **resume**, paste a **Google Form link** (job or internship application), and it **fills the form for you**, using **two models we train ourselves** plus simple rules. It never guesses: when unsure, it asks the user to check.

```
                 ┌──────────────────────────────┐
 Resume PDF ───► │ MODEL 1: NER extractor       │──► PROFILE (name, college, ...)
                 │ (fine-tuned BERT) + rules    │          │
                 └──────────────────────────────┘          │
                                                           ▼
 Google Form ──► parse questions ──► MODEL 2: field matcher ──► "this question asks for: phone"
 link                                (fine-tuned MiniLM)            │
                                                                    ▼
                                         copy value from profile ──► option matcher (for dropdowns/choices)
                                                                    │
                                                                    ▼
                                    AUTO (confident) / REVIEW (unsure) ──► user confirms ──► pre-filled link
```

- **Model 1: NER (Named Entity Recognition).** Reads resume text and tags words as NAME, COLLEGE, DEGREE, BRANCH, LOCATION, SKILL.
- **Model 2: field matcher (text classifier).** Reads a form question and says which profile field it asks for ("Mob. No." → phone), or `open_text` / `unsupported` when it should not be auto-filled.
- **Rules:** regex for email, phone, CGPA, GitHub, LinkedIn (rules beat models on these).
- **Safety:** confidence thresholds chosen on validation data. Low confidence becomes REVIEW, never a silent guess. The user always clicks Submit.

**Honest framing for the paper:** small trained models are cheap, private (run locally) and safe because they defer to the user, but they cover fewer fields than a large LLM. The paper reports this trade-off truthfully. (Earlier LLM baseline, optional to cite: on a 21-form / 231-question test with a fake profile, Nemotron 550B scored 100%, Nemotron 3.5 Lightning 30B 99.1%, and a 120B model 99.1%. That test used a different profile and setup, so cite it only as context, not as a head-to-head result.)

**No plan can promise results.** What this plan guarantees: every phase has a check, every known risk has a fallback (section 11), and nothing depends on luck or on teammates.

## 4. Verified facts from the earlier prototype (do not re-discover these)

These were tested on the user's machine and worked.

**Google Forms structure.** A Google Form's page contains a JS variable `FB_PUBLIC_LOAD_DATA_ = [...]` holding the whole form. Parse with a regex like `FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);\s*</script>` then `json.loads`. Then:
- `items = data[1][1]` is the list of form items.
- For each item: `item[1]` = question title, `item[3]` = type code, `item[4]` = list of sub-questions (skip the item if empty or missing, because section headers and images have none).
- For each sub-question `sub`: `sub[0]` = entry id (the pre-fill key is `entry.<sub[0]>`), `sub[1]` = list of options where each option is `[text, ...]`, `sub[2]` = required flag.
- Type codes: 0 short text, 1 paragraph, 2 multiple choice, 3 dropdown, 4 checkboxes, 5 linear scale, 7 grid, 9 date, 10 time, 13 file upload.
- Titles can have stray spaces. Always `.strip()` and collapse whitespace.
- If the page redirects to `accounts.google.com`, the form needs sign-in. Show a clear message. This is a documented limitation.
- Short links `forms.gle/...` redirect to the long `/viewform` link. Use the final URL.

**Pre-filled links.** `https://docs.google.com/forms/d/e/<FORM_ID>/viewform?usp=pp_url&entry.111=value&entry.222=value`. For checkboxes repeat the same key once per selected option. Values for multiple-choice, dropdown and checkboxes must match the option text exactly. URL-encode with `urllib.parse.urlencode(..., doseq=True)`. The "Other" option is not supported (known limitation). File uploads cannot be pre-filled (known limitation). This method filled text, paragraph, multiple choice, checkbox and dropdown fields correctly in a real browser.

**Fetching the page.** Playwright (Chromium) worked for loading and reading forms. Try plain `requests.get` with a normal browser `User-Agent` first, because it is simpler and avoids browser problems. If the variable is not found, fall back to Playwright.

**Environment pitfalls already hit (avoid them):**
- Never work inside `C:\Windows\system32` (permission errors). Use `D:\Projects\formfill2`.
- Environment variables reset in each new terminal. `$env:NVIDIA_API_KEY` holds the key; a separate `$env:NIM_MODEL` holds a model name. Do not mix them up.
- In PowerShell `fc` is not the file-compare tool; use `fc.exe`.
- JSON files break easily from curly quotes or a missing value. Validate with `python -c "import json; json.load(open('file.json', encoding='utf-8'))"`.
- The PyMuPDF package now prefers `import pymupdf` (the old `import fitz` still works but warns).
- Playwright's sync API breaks inside Streamlit on Windows (asyncio error). Always run Playwright in a separate subprocess (section 9, phase 7).

**Optional NVIDIA NIM usage** (only if the user wants LLM-generated paraphrases or an LLM baseline): OpenAI-compatible API at `https://integrate.api.nvidia.com/v1`; model names looked like `nvidia/nemotron-3-ultra-550b-a55b` and `nvidia/nemotron-3.5-lightning-30b-a3b`. Use a timeout (120 s) and retries. Not part of the core path.

## 5. Scope, targets and priority tiers

**In scope:** web-based Google Forms for job and internship applications, English only, text-based resume PDFs.
**Out of scope (state as limitations):** file uploads, the "Other" option, forms that need Google sign-in, scanned resumes (no OCR), grids/date/time/linear-scale auto-fill, non-Google forms, 10th/12th marks.

**Priority tiers (use this to decide what to cut):**
- **MUST:** field matcher trained (variant C) and evaluated; NER fine-tuned plus rules and evaluated; pipeline with AUTO/REVIEW; Streamlit demo producing a pre-filled link; results tables; README; paper draft.
- **SHOULD:** the 3-variant comparison (A/B/C); real-resume evaluation (10+ resumes); real-forms test set (Test B); threshold curve; ablations.
- **COULD:** Playwright screenshot in the demo; LLM baseline comparison; Hugging Face upload; NIM paraphrase augmentation.

**Aspirational targets (report whatever is actually achieved, never fake):**
- Field matcher macro-F1 ≥ 0.90 on the held-out test; auto-fill precision ≥ 98% at the chosen threshold (report coverage honestly).
- NER synthetic dev entity-F1 ≥ 0.90.
- Real resumes: value-level accuracy per field reported; email/phone/CGPA/links should be high because they are rules; name/college/degree/skills will be lower.

## 6. The schema (freeze this in Phase 1)

**17 classes** for the field matcher: 15 profile fields plus 2 non-fill classes.

| # | class | meaning / example questions | value comes from |
|---|---|---|---|
| 1 | `full_name` | Full Name, Candidate Name, Name of applicant | NER NAME, fallback: top line of resume |
| 2 | `email` | Email, Email ID, Mail address | regex |
| 3 | `phone` | Phone, Mobile No., Contact number | regex (10-digit Indian mobile; strip +91/spaces) |
| 4 | `college` | College, Institute, University name | NER COLLEGE |
| 5 | `degree` | Degree, Qualification, Course pursuing | NER DEGREE (normalized: B.Tech, B.E., BCA, M.Tech...) |
| 6 | `branch` | Branch, Stream, Department, Specialization | NER BRANCH or alias table (CSE, ECE, ...) |
| 7 | `year_of_study` | Current year, Which year are you in? | user selects in profile editor (not reliably on resumes; never calculate) |
| 8 | `graduation_year` | Passing out year, Batch, Expected graduation | rule on date ranges in the education section |
| 9 | `cgpa` | CGPA, Aggregate, GPA (out of 10) | regex; **percentage is NOT cgpa** |
| 10 | `city` | Current city, City you live in | NER LOCATION, split |
| 11 | `state` | State | LOCATION split plus an Indian-states lookup |
| 12 | `github` | GitHub URL/profile | regex |
| 13 | `linkedin` | LinkedIn URL/profile | regex |
| 14 | `skills` | Technical skills, Skills known | NER SKILL plus a skills-section parse (list) |
| 15 | `target_role` | Role applied for, Position, Preferred domain | user input in the profile editor |
| 16 | `open_text` | Why do you want this? Tell us about yourself, Describe a project | never auto-filled; shown as "write this yourself" |
| 17 | `unsupported` | DOB, gender, father's name, address, pincode, Aadhaar, PAN, stipend, notice period, availability, relocation, work mode, referral, resume link, 10th/12th marks, languages, nationality... | never auto-filled; shown as "not in profile" |

**Decision rules for ambiguous questions** (write these into `data/schema.json` and apply them consistently when labelling):
- "Location" or "City" → `city`; "State" → `state`; "Address" or "Pincode" → `unsupported`.
- "Year of passing / Batch / Graduation year" → `graduation_year`; "Current year / Year of study / Which year are you in" → `year_of_study`.
- "Percentage" or "Marks" → `unsupported` (only CGPA is supported).
- "Course / Degree / Qualification" → `degree`; "Branch / Stream / Department" → `branch`.
- "Resume link / Upload resume / Portfolio" → `unsupported`.
- Questions about willingness, availability, preferences, or personal details not in the schema → `unsupported`.
- Any free-writing question → `open_text`.

**NER tag set (BIO):** `NAME, COLLEGE, DEGREE, BRANCH, LOCATION, SKILL` (13 tags: `O` plus `B-` and `I-` for each type). Graduation year is handled by rule, not NER.
Important: **only the candidate's degree-granting college is `COLLEGE`.** School names (10th/12th), company names, project names and internship locations are `O`. Only the candidate's own location (header/address) is `LOCATION`.

## 7. Repository layout (create exactly this)

```
D:\Projects\formfill2\
  PROJECT_STATE.md          # paste the STATE block here after each phase
  README.md  requirements.txt  .gitignore
  data\
    schema.json
    phrasebank\             # base question phrasings per class (JSON)
    fm\                     # field-matcher splits: train.csv val.csv test_a.csv test_b.csv
    resumes_synth\          # synthetic resumes + labels
    ner\                    # tokenized NER data: train.json dev.json test.json
    real\                   # real resumes + gold profiles (NEVER commit)
  src\
    schema.py  make_fm_data.py  train_fm.py  eval_fm.py
    make_resumes.py  make_ner_data.py  train_ner.py
    rules.py  extract.py  option_matcher.py  gform.py  pipeline.py
  tools\
    parse_form.py  screenshot.py      # run as subprocesses
  app.py                    # Streamlit demo
  notebooks\                # Colab notebooks (NER training)
  models\                   # trained weights (NEVER commit)
  results\                  # metrics json/csv, plots, logs
  tests\                    # unit tests for rules and option matcher
  paper\                    # outline, tables, figures
```

`.gitignore` must contain: `models/`, `data/real/`, `venv/`, `__pycache__/`, `*.pt`, `*.safetensors`, `.env`, `*API key*`, `browser_profile/`.

## 8. Phases (the work)

Each phase lists: **Goal → Steps → Acceptance check → Fallback → Time.** Total ≈ 18 hours.

### Phase 0: Setup and risk checks (≈ 40 min)
**Steps**
1. Create `D:\Projects\formfill2` (not under `C:\Windows`). Open it in VS Code.
2. Check Python: `py --list`. Prefer **3.11 or 3.12** for the project venv. If only 3.14 exists, first test `pip install torch` in a throwaway venv; if no wheel exists, install Python 3.12 from python.org and use it (`py -3.12 -m venv venv`). Activate: `.\venv\Scripts\Activate.ps1` (if blocked: `Set-ExecutionPolicy -Scope Process Bypass`).
3. Install and pin: `torch transformers sentence-transformers scikit-learn seqeval pymupdf rapidfuzz pandas numpy matplotlib streamlit requests playwright pytest`. Then `playwright install chromium`. Save versions with `pip freeze > requirements.txt`.
4. Smoke test script `src/smoke.py`: print library versions, download `sentence-transformers/all-MiniLM-L6-v2` and `dslim/bert-base-NER` tokenizers, run one forward pass, print `OK`.
5. Colab check: open a notebook, set runtime to GPU, run `import torch; print(torch.cuda.is_available())`. If GPU is unavailable, note the fallback below.
6. Create the repo skeleton from section 7, `PROJECT_STATE.md`, and `.gitignore`. `git init`.

**Acceptance:** `smoke.py` prints `OK`; Colab prints `True` (or the fallback is chosen); skeleton exists.
**Fallbacks:** no torch for the local Python → use Python 3.12 venv; HF downloads blocked locally → download in Colab and copy files over; no Colab GPU → try Kaggle notebooks (free GPU) or train NER on CPU using `distilbert-base-cased` with fewer examples (see Phase 5).

### Phase 1: Freeze the schema (≈ 20 min)
**Steps:** write `data/schema.json` (17 classes, definitions, examples, decision rules from section 6, NER tag set, Indian states list, branch alias table such as `CSE = computer science (and engineering)`, `ECE = electronics and communication`, `EEE`, `MECH`, `CIVIL`, `IT`, `AIML`, `AIDS`), and `src/schema.py` to load it.
**Acceptance:** `python -c "from src.schema import *; print('OK')"` works; schema validated as JSON.
**Do not change the schema after this phase** except to fix real bugs (changing it later breaks datasets).

### Phase 2: Field-matcher dataset (≈ 2 to 2.5 h)
**Goal:** a labelled set of form questions with proper train/val/test separation.

**Steps**
1. **Phrase bank.** The assistant writes `data/phrasebank/<class>.json` with **base phrasings** per class: about 40 to 80 for each of the 15 profile fields, about 40 for `open_text`, and **150+ for `unsupported`** (many different topics). Include formal, casual, short, long, abbreviated and Indian-English styles ("Mob. No.", "Passing out year", "Name of the institution you are studying in"). Do not write them all as variations of the same sentence.
2. **Split at the BASE-PHRASE level before any augmentation:** 80% train, 20% val. This keeps validation phrasings truly unseen. Save the split.
3. **Augment train and val separately** with deterministic code (seed 42): prefixes ("Please enter your", "Enter", "Your"), suffixes ("*", "(required)", "as per records", ":"), numbering ("3."), casing changes, extra spaces, punctuation changes, light typos, and a type token. The **input text** is `"[<type>] <question>"`, for example `"[short_text] Mob. No."`, and types are drawn from `short_text, paragraph, multiple_choice, dropdown, checkboxes`. Target: about 3,000 to 5,000 training rows, with `unsupported` at most 35% of rows.
4. **Test A (held-out, real wording):** if the user still has the earlier validated forms (`tests/form_01..20.json`, 231 questions), derive labels with a script: `__ANY__` paragraphs → `open_text`; `null` → `unsupported`; non-null → find the profile field whose value equals the expected answer; for choice questions and ambiguous ones, list them for **manual labelling** (about 30% will need it). Check every label by hand against the schema rules. If those files are gone, build Test A by hand-labelling 150+ questions the user collects from real forms.
5. **Test B (optional but valuable):** 100+ questions copied from **real application forms the team did not write** (club, hackathon, internship forms; copy question text and type only). Hand-label them into `data/fm/test_b.csv`.
6. **Leak check script:** report exact and near-duplicate overlap (normalized text) between train and each test set; remove overlapping training rows. Report the overlap numbers (they go in the paper).
7. Print dataset statistics: rows per class and per split.

**Acceptance:** `train.csv`, `val.csv`, `test_a.csv` (and `test_b.csv` if built) exist; every class has ≥ 100 train rows (except where noted); leak report shows 0 exact overlaps; stats printed.
**Fallback:** if hand-labelling Test A takes too long, label a 150-question subset and say so. Never skip the leak check.

### Phase 3: Train and evaluate the field matcher (≈ 2 h)
**Three variants (all evaluated the same way):**
- **A (baseline, no deep learning):** TF-IDF char n-grams (2 to 5) + Logistic Regression.
- **B (frozen embeddings):** `all-MiniLM-L6-v2` sentence embeddings (frozen) + Logistic Regression (`class_weight="balanced"`, tune `C` on val).
- **C (the deep learning model, MAIN):** fine-tune `sentence-transformers/all-MiniLM-L6-v2` with a classification head (`AutoModelForSequenceClassification`, 17 labels). Starting settings: lr 5e-5, batch 32, epochs up to 8, weight decay 0.01, 10% warmup, max length 48, seed 42, class-weighted cross-entropy, keep the best epoch by **validation macro-F1** (early stopping). Log **train loss, val loss, val macro-F1 per epoch** to `results/fm_training_log.csv` and plot the curves. (A warning about newly initialized classifier weights is expected.)

**Evaluation (on val, Test A, and Test B if present):** accuracy, macro-F1, per-class precision/recall/F1, confusion matrix plot.
**Threshold:** compute the max-softmax confidence. On **validation only**, choose τ_fm = the smallest threshold with ≥ 98% auto-fill precision (auto-fill = predicted class is a profile field AND confidence ≥ τ_fm). Report the **precision-vs-coverage curve** and the numbers at τ_fm for each test set. Never tune thresholds on test data.
**Save:** model to `models/field_matcher/` (small), plus `results/fm_metrics.json`.

**Acceptance:** all three variants have metrics; C has training curves; a confusion matrix exists; τ_fm is saved in `models/field_matcher/config.json`.
**If C scores below 0.80 macro-F1:** (1) print the 30 worst errors and check for label conflicts in the data; (2) check the schema decision rules were applied consistently; (3) add more distinct phrasings for the weakest classes; (4) as last resort, report B as the main model and C as an honest comparison.
**Gate:** do not move on until one variant is usable (macro-F1 ≥ 0.80 on val and Test A).

### Phase 4: Resume side, part 1: synthetic resumes, rules, real test data (≈ 2.5 h)
**Steps**
1. **Synthetic resume generator** `src/make_resumes.py` (seed 42): produce **3,000 train / 300 dev / 300 test** resumes as text with exact span labels. Use **at least 6 different layouts**, varied section headers (Education / Academic Details / Qualifications), varied date formats ("2023 - 2027", "Aug 2023 – May 2027"), two-column-like line interleaving, random bullets (•, -, *, ▪), UPPERCASE headers, missing sections, varied phone formats (`+91 98765 43210`, `98765-43210`), email variants, and CGPA label variants ("CGPA", "GPA", "Aggregate"; also decoys such as "Percentage: 85%" that must NOT become cgpa).
   Vocabulary lists written by the assistant: 300+ Indian first names and surnames, 150+ colleges (with short forms and lowercase variants), degree × branch combinations, 100+ skills, 60+ cities with states, project titles, company names, school names. **Negatives are essential:** schools, companies and project names appear as `O`; only the candidate's own college and own location are tagged.
2. **Rules module** `src/rules.py` (regex and small lookups): email, phone (normalize to 10 digits), CGPA (handle "8.4/10", "CGPA: 8.4", reject percentages), GitHub URL, LinkedIn URL, graduation year (latest year in the education date range), branch alias normalization, state lookup. Write **unit tests** in `tests/` with at least 25 edge cases and run `pytest`.
3. **PDF text extraction** helper using `pymupdf`: `page.get_text("text", sort=True)`; return plain text. Provide a paste-text fallback in the demo for jumbled or scanned PDFs.
4. **Real test data (start now, finish before Phase 8):** collect **10 to 15 real student resumes** (PDF, with the owners' consent: the user's own plus classmates). Store in `data/real/` (never commit). For each, hand-write a **gold profile JSON** using only the 15 profile fields. These resumes are used **only for testing**, never for training.

**Acceptance:** generator produces files; label spot-check of 10 random synthetic resumes looks correct; `pytest` passes; at least the user's own resume plus its gold profile exist.
**Fallback:** if fewer than 10 real resumes can be collected, evaluate on what exists (even 5) and say so in the paper.

### Phase 5: NER training and extraction (≈ 2.5 h including waiting)
**Steps**
1. `src/make_ner_data.py`: convert the synthetic resumes into word-level BIO labels. **Chunk each resume into windows of at most ~200 words** (BERT's limit is 512 tokens) and keep line breaks as tokens or boundaries consistently at training and inference.
2. Colab notebook `notebooks/train_ner.ipynb`: install `seqeval`, upload the data (Drive or a zip), fine-tune **`dslim/bert-base-NER`** for token classification with the new 13-tag label map (`ignore_mismatched_sizes=True`). Align labels to word pieces: label the first sub-token of each word; set the rest to -100. Starting settings: lr 3e-5, batch 16, epochs 4, max length 256, fp16 on GPU, seed 42, evaluate each epoch with **seqeval** entity-level precision/recall/F1. Save the training log and curves.
3. Download the trained model folder to `models/ner/` (≈ 430 MB, never commit it).
4. `src/extract.py`: sliding-window inference over a resume, merge predictions into entity spans, compute each span's confidence (mean token probability), and choose **one value per field** (highest confidence; for names prefer spans near the top of the document). Combine with the rules from `rules.py` to produce the profile dict `{field: {"value":..., "confidence":..., "source": "ner|rule"}}`. Fields not found are `null`. Choose τ_ner on the **synthetic dev set** (and sanity-check on real resumes).
5. **Evaluate:**
   - Synthetic test: seqeval entity-level F1 per type (label it *synthetic*).
   - **Real resumes: value-level accuracy per field** against gold profiles (normalize: case-insensitive, strip punctuation, phone = last 10 digits, CGPA numeric). Report accuracy and coverage (fraction non-null) per field. Compare **rules-only vs NER+rules** (ablation).

**Acceptance:** model trained with a saved training log; extraction runs on the user's own resume and prints a profile; the evaluation table exists.
**Fallbacks:**
- No Colab/Kaggle GPU → train `distilbert-base-cased` on CPU with ~1,000 resumes and 2 epochs (slow but possible), or reduce to `max length 128`.
- Synthetic dev F1 < 0.85 → check label alignment (most common bug), chunking, and that negatives are present.
- Real-resume accuracy much lower than synthetic (expected to some degree) → add more layout and noise variety to the generator and retrain once; if it is still weak, report it honestly and rely on the editable profile in the demo. Never train on the real resumes (they are the test).

### Phase 6: Pipeline, option matcher and end-to-end evaluation (≈ 2 h)
**Steps**
1. `src/option_matcher.py`: given a profile value and a list of options, return the best option and a score. Normalize text (case, punctuation, "and"/"&"), use the alias table (`CSE` ↔ computer science), `rapidfuzz` similarity, and special handling for year of study ("3rd year" ↔ "Third Year") and degree ("B.Tech" ↔ "BTech" ↔ "B.E."). For checkboxes (skills), select every option that clearly contains a profile skill; if none, REVIEW. Threshold τ_opt chosen on a small hand-made dev list. **Unit tests required.**
2. `src/pipeline.py`: for every parsed question:
   - predict class and confidence with the field matcher;
   - if class is `open_text` or `unsupported` → status `REVIEW`, reason "write this yourself" or "not in profile";
   - elif confidence < τ_fm → `REVIEW` with the suggested field;
   - elif the profile value is missing or its confidence < τ_ner → `REVIEW` (reason "missing in profile");
   - elif the question is a choice type → option matcher; no match ≥ τ_opt → `REVIEW`;
   - else → `AUTO` with the answer.
   Output a list of `{entry_id, question, type, predicted_field, confidence, answer, status, reason}`.
3. **End-to-end evaluation:** run the pipeline for **each real resume × each labelled test form** (e.g., 10 resumes × 21 forms). The expected answer for a question = the resume's gold profile value for the question's gold class (`open_text` and `unsupported` expect REVIEW). Report: **auto-fill precision** (correct among AUTO), **coverage** (fraction of fillable questions that were AUTO), **REVIEW rate**, wrong-fill rate, and a per-field breakdown. Also report a **field-matcher-only** end-to-end using a clean profile (isolates Model 2).

**Acceptance:** pipeline runs on the user's resume + a real Google Form and prints a status table; the end-to-end evaluation produces `results/e2e_metrics.json`.
**Fallback:** if end-to-end precision is low, inspect the worst 30 wrong fills; the cause is usually the option matcher or a wrong profile value, not the classifier.

### Phase 7: Google Forms parser, pre-fill builder and Streamlit demo (≈ 2.5 h)
**Steps**
1. `src/gform.py`: `parse_form(url)` (section 4 facts; try `requests` first, then fall back to the Playwright subprocess), `build_prefill_link(form_url, answers)`. Run Playwright only inside `tools/parse_form.py` and `tools/screenshot.py`, called with `subprocess.run([sys.executable, ...], timeout=90)` and JSON on stdout. **Never call Playwright directly inside Streamlit.**
2. `app.py` (Streamlit), three steps on one page:
   - **Step 1, Profile:** upload resume PDF (or paste text) → extracted profile in an **editable table** (value + confidence). The user also sets `year_of_study` and `target_role` here.
   - **Step 2, Form:** paste the form link → questions parsed → mapping table showing question, predicted field, confidence, proposed answer, and status (AUTO green, REVIEW amber). The user can edit any answer.
   - **Step 3, Fill:** "Generate pre-filled link" → clickable link (this is the primary result and always works). Optional "Preview" button runs the screenshot subprocess.
   - A **"Clear my data"** button; no personal data written to disk except temporary files that are deleted.
3. Make **3 demo Google Forms** (open access, no sign-in, no uploads) for the demo and screenshots. Test on every question type in scope.

**Acceptance:** `streamlit run app.py` works end to end: resume in, form link in, pre-filled link out, and opening the link shows the answers filled in a real browser.
**Fallbacks:** form parse fails → show the error and offer "paste questions manually"; form requires sign-in → clear message; Playwright preview fails → still show the pre-filled link.

### Phase 8: Final experiments, tables and figures (≈ 1.5 h)
Run once, with fixed seeds, and save everything in `results/`:
1. **Field matcher variants** A/B/C on val, Test A, Test B (accuracy, macro-F1).
2. **Training-set-size curve:** train C on 25%, 50%, 100% of training data → macro-F1 plot (shows data efficiency).
3. **With vs without the type token** (small ablation).
4. **Threshold curve:** precision vs coverage for τ_fm.
5. **Extraction:** rules-only vs NER+rules on real resumes; per-field accuracy.
6. **End-to-end** table (section 6, Phase 6).
7. **Efficiency:** model sizes (MB), parameter counts, and latency per form and per resume on the user's laptop CPU.
8. **Error analysis:** list the 20 most informative wrong or REVIEW cases and group them by cause.
9. (COULD) LLM baseline row from the earlier run, with the caveat from section 3.

**Acceptance:** `results/` contains the metrics JSONs, CSV logs, and PNG plots (training curves, confusion matrix, coverage curve, size curve).

### Phase 9: Documentation, GitHub, paper, resume (≈ 2.5 h)
1. **README:** what it does, install, how to run the demo, how to retrain, results table (real numbers), limitations, credits.
2. **GitHub:** verify `.gitignore`, make sure no real resumes, keys or model weights are staged (`git status`), then push. Put the large models on Hugging Face Hub or Google Drive and link them.
3. **Paper (6 to 8 pages)**, outline:
   - Title (for example: *FormFill: Privacy-Preserving Automatic Filling of Job Application Forms with Fine-Tuned NER and Question-Field Matching Models*).
   - Abstract; Introduction (problem, why trained small models, contributions).
   - Related work (existing systems reviewed: AI-Form-Filling-Assistant, IntelliFill, form_auto, pdf-ocr-llm, Open-DocLLM, and a tutorial on form-filling agents).
   - Method: schema, data generation, Model 1, Model 2, rules, pipeline with confidence thresholds and human-in-the-loop, option matching.
   - Experimental setup: datasets and splits, leakage controls, metrics, baselines.
   - Results: field matcher variants, size curve, extraction, end-to-end, ablations, efficiency.
   - Error analysis; Limitations (section 5 list, small real-resume set, synthetic-data bias); Ethics (personal data handled locally, user reviews and submits); Conclusion and future work.
   - Figures: pipeline diagram, training curves, confusion matrix, coverage curve, size curve. Tables: dataset stats, matcher variants, extraction per field, end-to-end, ablations.
   - Be careful with claims: say "on our test sets"; mark synthetic vs real; mention small test sizes and show confidence intervals if possible (bootstrap).
4. **Resume bullets:** only after real numbers exist (template: "Fine-tuned BERT-based NER and MiniLM question classifiers; X% auto-fill precision at Y% coverage on N real resumes/forms; built Streamlit demo generating pre-filled Google Forms").
5. **Demo script (3 minutes)** for the review: upload resume → edit profile → paste form link → show AUTO/REVIEW table → generate link → open filled form → mention the trade-off versus LLMs.

## 9. Anti-leakage and evaluation rules (strict)

- Split the phrase bank at the **base-phrase level**, then augment. Never augment before splitting.
- Test A, Test B and real resumes are **never** used for training, threshold choice, or hyperparameter tuning. Only the validation set is.
- Report train/test overlap numbers.
- Real resumes are test-only. Synthetic test results are labelled *synthetic* everywhere.
- Fixed seeds (42) and saved split files so every number can be reproduced.
- Report macro-F1 (not only accuracy), because `unsupported` dominates.

## 10. Day-by-day schedule (≈ 20 hours available)

| When | Phases | Hours | Gate to pass before continuing |
|---|---|---|---|
| **Day 1 morning** | 0, 1, 2 | ≈ 3.5 | Environment works; dataset and leak check done |
| **Day 1 midday** | 3 | ≈ 2 | Field matcher usable (macro-F1 ≥ 0.80) |
| **Day 1 afternoon/evening** | 4, start 5 (launch Colab training, work on rules/tests while it runs) | ≈ 4 | Rules tests pass; NER training launched |
| **Day 2 morning** | finish 5, 6 | ≈ 4 | Profile extraction works on own resume; pipeline prints a status table |
| **Day 2 afternoon** | 7, 8 | ≈ 4 | Demo works end to end; metrics saved |
| **Day 2 evening** | 9 | ≈ 2.5 | README + GitHub + paper draft + resume |

**Cut list (if behind, cut in this order):** (1) LLM baseline row; (2) HF upload and screenshot preview; (3) size-curve and type-token ablations; (4) Test B; (5) variant A of the field matcher. **Never cut:** the leak checks, real-resume testing (even 5 resumes), the training logs, or the limitations section.

## 11. Dead-end register (known risks and the planned response)

| Risk | What to do |
|---|---|
| Python 3.14 has no PyTorch wheel | Install Python 3.12 and use a venv; heavy training in Colab |
| No Colab GPU / quota | Kaggle GPU notebook; or CPU with `distilbert-base-cased`, fewer examples |
| HuggingFace download blocked locally | Download in Colab, save and copy the folder over |
| `transformers` argument names differ | Print version; use `eval_strategy` or `evaluation_strategy` as the version accepts |
| NER learns layouts, fails on real resumes | Many layouts/noise in the generator; negatives; rules fallback; editable profile; honest reporting |
| School/company names tagged as COLLEGE | Include them as `O` negatives in the generator; check on real resumes |
| Percentage mistaken for CGPA | Rule rejects `%`; decoys in synthetic data; unit tests |
| Scrambled text from two-column PDFs | `get_text(sort=True)`; paste-text fallback in the demo |
| Dataset leakage inflating scores | Base-phrase split, overlap report, held-out Test A/B, real resumes as test-only |
| `unsupported` class dominates | Class-weighted loss, cap at 35% of rows, report macro-F1 |
| Over-confident softmax | Choose thresholds on validation; report coverage curve; optional temperature scaling |
| Dropdown/option mismatch (CSE vs Computer Science) | Alias table, fuzzy matching, unit tests, REVIEW on low score |
| Pre-filled link does not fill a field | Values must equal option text exactly; checkboxes repeat the key; skip "Other" and uploads and say so |
| Form needs Google sign-in | Detect `accounts.google.com`; show a clear message; documented limitation |
| Playwright crashes inside Streamlit | Run in a subprocess only |
| Model weights too big for GitHub | `.gitignore`; host on HF Hub or Drive |
| Personal data in the repo | `.gitignore` `data/real/`; check `git status` before every push |
| Running out of time | Use the cut list; keep the MUST tier safe |
| Teammates do not deliver | Nothing in the critical path depends on them (section 12) |

## 12. Optional teammate tasks (non-blocking, each has a fallback)

If the user wants help, hand these out as separate tasks (the assistant can write a short, strict instruction sheet for each, with an exact file format):
1. **Real resumes + gold profiles:** 10 to 15 student resumes (PDF) with consent, and one gold profile JSON each in the 15-field schema. *Fallback: the user's own resume plus whatever arrives.*
2. **Real forms test set (Test B):** question text and type from 15+ real application forms, as a CSV `question,type` (the user or assistant labels them). *Fallback: skip Test B.*
3. **Demo forms:** 3 Google Forms with open access (no sign-in, no uploads). *Fallback: the user makes them in 20 minutes.*

## 13. Credits to include in README and paper

`sentence-transformers/all-MiniLM-L6-v2` (Sentence-Transformers), `dslim/bert-base-NER` (fine-tuned from BERT; cite BERT and the model card), Hugging Face Transformers, scikit-learn, seqeval, PyMuPDF, RapidFuzz, Streamlit, Playwright. If any public resume dataset is used, cite it. Prior form-filling projects reviewed: AI-Form-Filling-Assistant, IntelliFill, form_auto, pdf-ocr-llm, Open-DocLLM. List which team member built which part (the paper's contributions section must be accurate).

## 14. STATE block (assistant prints this after every phase)

```
PROJECT STATE (paste into PROJECT_STATE.md)
Date/time:
Current phase:            (number and name)
Completed phases:         
Environment:              Python version, venv path, GPU source (Colab/Kaggle/CPU)
Key files created:        
Data stats:               rows per split, classes, overlap numbers
Models trained:           name, epochs, best epoch, val metric, saved path
Thresholds:               tau_fm=  tau_ner=  tau_opt=
Latest metrics (real or synthetic, labelled):
Open problems / decisions pending:
Next action (exact command or file to create):
```

## 15. Kickoff message (the user pastes this in the new chat with this file attached)

> I'm building FORMFILL v2. The attached file `FORMFILL_PROJECT_PLAN.md` is the full plan and your working rules. Read it completely. Follow section 1 (rules) strictly: one phase at a time, complete files, simple words, PowerShell commands, no invented numbers. We start with **Phase 0**. First tell me in 5 lines what you understood about the project and what Phase 0 will check, then give me the first commands. After each phase I will paste my outputs, and you will give me the STATE block. I have about 2 days, so use the cut list if we fall behind.

*(After a break or in a new session, the user attaches this file plus `PROJECT_STATE.md` and says: "Continue from the state file, next action as written.")*

# FormFill results

All numbers come from the scripts in this repository (seed 42). SYNTHETIC = generated data, REAL = real resumes and forms.

## 1. Field matcher (question -> profile field)

| variant | val acc | val macro-F1 | test_a acc | test_a macro-F1 |
|---|---|---|---|---|
| A: TF-IDF + LogReg (baseline) | 0.942 | 0.950 | 0.957 | 0.977 |
| B: frozen MiniLM + LogReg | 0.926 | 0.938 | 0.905 | 0.950 |
| C: fine-tuned MiniLM (main model) | 0.945 | 0.956 | 0.940 | 0.973 |

val = held-out phrasings (synthetic wording). test_a = real wording from 21 earlier forms (116 unique questions, no `branch` rows).

Confidence threshold tau_fm = 0.89, chosen on val only (target precision 0.98).

| set | auto-fill precision | coverage (of all questions) | auto-filled |
|---|---|---|---|
| val | 98.1% | 71.6% | 481 |
| test_a | 98.4% | 53.4% | 62 |

### Leakage check (train vs evaluation sets)

| set | rows | exact / near overlap before removal | after removal |
|---|---|---|---|
| val | 672 | 11 / 50 | 0 / 0 |
| test_a | 116 | 62 / 67 | 0 / 0 |

Training rows 4758 -> 4316 (442 removed). Label conflicts inside train: 0.

## 2. NER model (SYNTHETIC resumes only)

| entity | dev F1 | test F1 |
|---|---|---|
| NAME | 1.000 | 1.000 |
| COLLEGE | 0.942 | 0.993 |
| DEGREE | 1.000 | 1.000 |
| BRANCH | 1.000 | 1.000 |
| LOCATION | 0.969 | 0.994 |
| SKILL | 1.000 | 1.000 |
| overall entity F1 | 0.995 | 0.999 |

## 3. Resume extraction on REAL resumes

Scored resumes: 13 (scanned PDFs without text are excluded, no OCR).

| field | n (gold present) | first run (untuned) | after error fixes | rules only |
|---|---|---|---|---|
| full_name | 13 | 92.9% | 100.0% | 0.0% |
| email | 13 | 92.9% | 100.0% | 100.0% |
| phone | 13 | 100.0% | 100.0% | 100.0% |
| college | 13 | 78.6% | 100.0% | 0.0% |
| degree | 13 | 92.9% | 100.0% | 0.0% |
| branch | 13 | 78.6% | 100.0% | 0.0% |
| graduation_year | 8 | 80.0% | 100.0% | 100.0% |
| cgpa | 12 | 76.9% | 100.0% | 100.0% |
| city | 7 | 100.0% | 100.0% | 0.0% |
| state | 8 | 63.6% | 100.0% | 0.0% |
| github | 9 | 100.0% | 100.0% | 100.0% |
| linkedin | 11 | 100.0% | 100.0% | 100.0% |

Mean field accuracy: first run 0.880, after fixes 1.000.
Skills: mean recall 0.815, mean precision 0.619.

The first run is the untuned result. The later run was tuned on the same resumes (error analysis, gold-label corrections), so it is an upper bound.

## 4. End-to-end form filling (REAL resumes x earlier forms)

13 resumes x 21 forms.

| mode | questions | fillable | AUTO | precision | coverage of fillable | wrong fills | REVIEW rate |
|---|---|---|---|---|---|---|---|
| full pipeline (extracted profile) | 2938 | 1591 | 1578 | 99.6% | 99.2% | 6 | 46.3% |
| gold profile (matchers only) | 2938 | 1591 | 1588 | 100.0% | 99.8% | 0 | 45.9% |

Bootstrap 95% over resumes (full pipeline): precision 99.0% to 100.0%, coverage 98.2% to 99.8%.
Before the ID-word rule: full pipeline precision 99.6% (6 wrong fills), gold profile 100.0%.

Rule overrides (ID words, 10th/12th marks) were added after error analysis on these same forms.

## 5. Efficiency (CPU only, this laptop)

| model | size on disk (MB) | parameters (M) |
|---|---|---|
| field matcher (MiniLM) | 92 | 22.7 |
| resume NER (BERT-base) | 432 | 107.7 |

Per resume: PDF text 0.02 s + NER and rules 0.08 s. Per form (21 forms, about 11 questions): 0.01 s.

## Figures in results/

- cm_A_tfidf_test_a.png
- cm_A_tfidf_val.png
- cm_B_frozen_test_a.png
- cm_B_frozen_val.png
- cm_C_finetuned_test_a.png
- cm_C_finetuned_val.png
- fm_coverage_curve.png
- fm_training_curves.png
- ner_training_curves.png
PROJECT STATE
Current phase:            7 (Streamlit app), starting
Completed phases:         0, 1, 2, 3, 4, 5, 6a, 6b, 6c
Thresholds:               tau_fm=0.89, tau_opt=85, tau_ner=0.5 (floor)
Pipeline results (2938 questions, 13 resumes x 21 forms, after ID-word rule; rule written after error analysis on same set):
                          Mode 1 extracted: precision 99.6%, coverage of fillable 99.2%, 6 wrong fills (all skills)
                          Mode 2 gold profile: precision 100%, 0 wrong fills
Known limits:             skills (recall ~0.82, precision ~0.62); grouped skill options go to REVIEW; scanned PDFs not supported; no clean held-out real resumes
Next action:              Phase 7: app.py (Streamlit)
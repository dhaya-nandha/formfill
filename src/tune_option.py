import json
from pathlib import Path

from src.option_matcher import match_option

CFG = Path(__file__).resolve().parent.parent / "data" / "option_config.json"
DEV = [
    ("year_of_study", "3rd Year", ["1st year", "2nd year", "3rd year", "4th year"], "3rd year"),
    ("year_of_study", "4", ["Year 1", "Year 2", "Year 3", "Year 4"], "Year 4"),
    ("year_of_study", "2nd Year", ["First", "Second", "Third"], "Second"),
    ("year_of_study", "3rd Year", ["Final Year", "Pre-final Year"], None),
    ("degree", "B.Tech", ["B.Tech", "B.E.", "BCA"], "B.Tech"),
    ("degree", "B.E.", ["B.Tech", "BCA"], None),
    ("degree", "BCA", ["Bachelor of Computer Applications", "Bachelor of Science"], "Bachelor of Computer Applications"),
    ("degree", "M.Tech", ["B.Tech", "M.Tech", "MBA"], "M.Tech"),
    ("branch", "ECE", ["ECE", "EEE", "CSE"], "ECE"),
    ("branch", "CSE", ["Computer Science", "Computer Science and Engineering"], None),
    ("branch", "AIML", ["AI & ML", "Data Science"], "AI & ML"),
    ("branch", "MECH", ["Mechanical", "Civil"], "Mechanical"),
    ("college", "VIT-AP University", ["VIT-AP", "VIT Vellore"], None),
    ("college", "IIT Madras", ["Indian Institute of Technology Madras", "IIT Madras"], "IIT Madras"),
    ("state", "Karnataka", ["Karnataka", "Kerala"], "Karnataka"),
    ("state", "Telangana", ["Andhra Pradesh", "Tamil Nadu"], None),
    ("graduation_year", "2027", ["2027", "2028"], "2027"),
    ("graduation_year", "2027", ["2024", "2025"], None),
    ("city", "Vellore", ["Vellore", "Vellur"], "Vellore"),
    ("target_role", "AI Engineer", ["AI Engineer", "AI Engineering Intern"], "AI Engineer"),
    ("target_role", "ML Engineer", ["AI Engineer", "Data Analyst"], None),
    ("target_role", "Data Analyst", ["Data Analyst Intern", "Data Scientist"], None),
]

print(f"{'tau':>5}{'correct':>9}{'wrong fills':>13}{'missed':>8}")
best = None
for tau in range(60, 101, 5):
    wrong = missed = ok = 0
    for field, value, options, expected in DEV:
        got = match_option(field, value, options, tau=tau)["option"]
        if got == expected:
            ok += 1
        elif got is None:
            missed += 1
        else:
            wrong += 1
    print(f"{tau:5}{ok:9}{wrong:13}{missed:8}")
    if wrong == 0 and best is None:
        best = tau
print(f"\nchosen tau_opt = {best} (smallest threshold with 0 wrong fills on the dev list)")
if best is not None:
    json.dump({"tau_opt": best, "cases": len(DEV)}, open(CFG, "w"))
    print("saved to data/option_config.json")
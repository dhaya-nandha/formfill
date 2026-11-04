import json
import re
import shutil
from pathlib import Path

import pymupdf

from src import rules
from src.pdf_text import extract_text
from src.vocab_people_places import CITIES

REAL = Path(__file__).resolve().parent.parent / "data" / "real"
BACKUP = REAL / "gold_backup"
BACKUP.mkdir(exist_ok=True)
GH = re.compile(r"(?i)^https?://(?:www\.)?github\.com/[A-Za-z0-9][A-Za-z0-9\-]{0,38}/?$")
LI = re.compile(r"(?i)linkedin\.com/in/[^/?#]+")
CITY_WORDS = sorted({c for c, _ in CITIES} | {"Bangalore"})

pdfs = [p for p in sorted(REAL.glob("*.pdf")) if (p.parent / (p.stem + ".gold.json")).exists()]
for i, pdf in enumerate(pdfs, 1):
    gp = pdf.parent / (pdf.stem + ".gold.json")
    gold = json.load(open(gp, encoding="utf-8"))
    with pymupdf.open(str(pdf)) as doc:
        uris = [l["uri"] for page in doc for l in page.get_links() if l.get("uri")]
    text = extract_text(pdf)
    lines = [l for l in text.splitlines() if l.strip()]
    notes, changed = [], False

    gh = next((u for u in uris if GH.match(u)), None)
    li = next((u for u in uris if LI.search(u)), None)
    for field, url, norm in (("github", gh, rules.extract_github), ("linkedin", li, rules.extract_linkedin)):
        if url and not gold.get(field):
            if not (BACKUP / gp.name).exists():
                shutil.copy(gp, BACKUP / gp.name)
            gold[field] = norm(url)
            notes.append(f"added {field} from the PDF hyperlink")
            changed = True
    if changed:
        json.dump(gold, open(gp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    g = gold.get("cgpa")
    if g is not None and str(g) not in text:
        shown = [l[:80] for l in lines if re.search(r"(?i)cgpa|gpa|aggregate", l)][:2]
        notes.append(f"CHECK CGPA: gold={g} but the PDF says: {shown}")
    if not gold.get("city"):
        found = []
        for w in CITY_WORDS:
            for n, l in enumerate(lines, 1):
                if re.search(rf"(?i)\b{w}\b", l):
                    found.append(f"{w} (line {n})")
                    break
        if found:
            notes.append(f"gold city is empty, city names in the PDF: {found[:4]}  (lines 1-6 = header)")
    print(f"#{i:02d}  {pdf.name}")
    for n in notes:
        print("      ", n)
print("\nBackups of changed gold files are in data/real/gold_backup/")
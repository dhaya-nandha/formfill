import re
import sys
from pathlib import Path

import pymupdf

from src import rules
from src.extract import extract_all
from src.pdf_text import extract_text

REAL = Path(__file__).resolve().parent.parent / "data" / "real"
import json


def resumes():
    return [p for p in sorted(REAL.glob("*.pdf")) if (p.parent / (p.stem + ".gold.json")).exists()]


def visible_and_links(pdf):
    with pymupdf.open(str(pdf)) as doc:
        visible = "\n".join(page.get_text() for page in doc)
        uris = [l.get("uri", "") for page in doc for l in page.get_links() if l.get("uri")]
    return visible, uris


def link_status(pdf):
    vis, uris = visible_and_links(pdf)
    out = []
    for name, fn, dom in (("github", rules.extract_github, "github.com"),
                          ("linkedin", rules.extract_linkedin, "linkedin.com")):
        out.append(f"{name}: visible text={fn(vis) is not None}, hyperlink={any(dom in u.lower() for u in uris)}")
    return " | ".join(out)


def main():
    pdfs = resumes()
    if len(sys.argv) > 1 and sys.argv[1] == "links":
        for i, pdf in enumerate(pdfs, 1):
            gold = json.load(open(pdf.parent / (pdf.stem + ".gold.json"), encoding="utf-8"))
            print(f"#{i:02d} gold github={'yes' if gold.get('github') else 'none'}, "
                  f"linkedin={'yes' if gold.get('linkedin') else 'none'} || {link_status(pdf)}")
        return
    for k in [int(a) for a in sys.argv[1:]]:
        pdf = pdfs[k - 1]
        gold = json.load(open(pdf.parent / (pdf.stem + ".gold.json"), encoding="utf-8"))
        text = extract_text(pdf)
        profile, spans, _ = extract_all(text)
        fields = ("college", "degree", "branch", "city", "state", "graduation_year", "cgpa")
        print(f"\n===== #{k:02d} =====")
        print("gold:", {f: gold.get(f) for f in fields})
        print("pred:", {f: profile[f]["value"] for f in fields})
        print("education lines:")
        for ln in rules._education_lines(text)[:10]:
            print("   ", ln[:100])
        print("cgpa lines:")
        for ln in [l for l in text.splitlines() if re.search(r"(?i)cgpa|gpa|aggregate", l)][:4]:
            print("   ", ln[:100])
        print("spans:")
        for s in spans:
            if s["type"] in ("COLLEGE", "DEGREE", "BRANCH", "LOCATION"):
                print(f"    {s['type']:9} {s['text']!r} [{s['conf']:.2f}] @{s['start']}")


if __name__ == "__main__":
    main()
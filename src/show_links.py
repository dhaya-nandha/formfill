import re
from pathlib import Path

import pymupdf

REAL = Path(__file__).resolve().parent.parent / "data" / "real"
private = []
pdfs = [p for p in sorted(REAL.glob("*.pdf")) if (p.parent / (p.stem + ".gold.json")).exists()]
for i, pdf in enumerate(pdfs, 1):
    with pymupdf.open(str(pdf)) as doc:
        uris = [l["uri"] for page in doc for l in page.get_links() if l.get("uri")]
    shown = []
    for u in uris:
        m = re.match(r"(?i)https?://(?:www\.)?([^/?#]+)/?([^?#]*)", u)
        if not m:
            continue
        host, path = m.group(1).lower(), [x for x in m.group(2).split("/") if x]
        if "github.com" in host:
            shown.append("github.com/" + "/".join("<id>" for _ in path[:2]))
        elif "linkedin.com" in host:
            shown.append("linkedin.com/" + (path[0] + "/<id>" if path else ""))
        else:
            continue
        private.append(f"#{i:02d} {u}")
    print(f"#{i:02d}", shown or "no github/linkedin hyperlink")
(REAL / "links.txt").write_text("\n".join(private), encoding="utf-8")
print("\nFull URLs saved in data/real/links.txt (private, git-ignored)")
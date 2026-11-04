import re
import sys

import pymupdf

_PRIVATE_USE = re.compile(r"[\ue000-\uf8ff\ufffd\u25a1\u25aa\u25ab]")


def _despace_line(line):
    """'E D U C A T I O N' -> 'EDUCATION' (lines made only of single characters)."""
    tokens = line.split()
    if len(tokens) >= 4 and all(len(t) == 1 and (t.isalpha() or t == "&") for t in tokens):
        return "".join(tokens)
    return line


def _links(doc):
    urls = []
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if uri and uri.lower().startswith(("http://", "https://")) and uri not in urls:
                urls.append(uri)
    return urls


def extract_text(source):
    """source = file path or PDF bytes. Returns plain text, one line per text line.
    Hyperlink URLs found in the PDF are appended at the end, one per line."""
    if isinstance(source, (bytes, bytearray)):
        doc = pymupdf.open(stream=bytes(source), filetype="pdf")
    else:
        doc = pymupdf.open(str(source))
    with doc:
        pages = [page.get_text("text", sort=True) for page in doc]
        urls = _links(doc)
    text = "\n".join(pages).replace("\u00a0", " ").replace("\u200b", "")
    text = _PRIVATE_USE.sub("•", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [_despace_line(ln) for ln in lines]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    if urls:
        text += "\n\n" + "\n".join(urls)
    return text


def looks_scanned(text):
    """Very little text usually means a scanned image PDF (no OCR in this project)."""
    return len(text.strip()) < 100


if __name__ == "__main__":
    from src.rules import extract_rule_fields

    if len(sys.argv) < 2:
        print("usage: py -m src.pdf_text <path-to-pdf>")
        raise SystemExit(1)
    txt = extract_text(sys.argv[1])
    print(f"characters: {len(txt)} | lines: {len(txt.splitlines())}")
    if looks_scanned(txt):
        print("WARNING: almost no text found. This may be a scanned PDF (not supported).")
    lines = txt.splitlines()
    print("\n--- first 12 lines ---")
    print("\n".join(lines[:12]))
    print("\n--- last 6 lines ---")
    print("\n".join(lines[-6:]))
    print("\n--- rule-based fields ---")
    for k, v in extract_rule_fields(txt).items():
        print(f"{k:16} {v}")
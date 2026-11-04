import re
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

from src import rules
from src.chunking import NL, make_windows, text_to_words
from src.schema import INDIAN_STATES, NER_ID2TAG, PROFILE_FIELDS
from src.vocab_people_places import CITIES

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "ner"
MAXLEN, MAXW = 320, 100
_state = {}
_DEG_SEP = re.compile(
    r"(?i)(?<![A-Za-z])(b\.?\s?tech\.?|b\.\s?e\.?|bca|b\.?\s?sc\.?|m\.?\s?tech\.?|mca|m\.?\s?sc\.?|mba)"
    r"\s*[-–—:]\s*(?=[A-Za-z])")


def _prep(text):
    """'B.Tech-Computer Science' -> 'B.Tech - Computer Science' (words stay separate)."""
    return _DEG_SEP.sub(r"\1 - ", text)


def _is_state_fragment(t):
    f = _flat(t)
    return len(f) >= 5 and any(f != _flat(s) and f in _flat(s) for s in INDIAN_STATES)


def _pick_branch(spans, degree_pos):
    cands = [s for s in spans if s["type"] == "BRANCH" and s["text"]]
    if not cands:
        return None
    if degree_pos is not None:
        near = [s for s in cands if degree_pos - 5 <= s["start"] <= degree_pos + 30]
        known = [s for s in near if rules.normalize_branch(s["text"])]
        if known:
            return min(known, key=lambda s: s["start"])
        if near:
            return max(near, key=lambda s: s["conf"])
    return max(cands, key=lambda s: s["conf"])


def load_model():
    if not _state:
        _state["tok"] = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
        _state["dev"] = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _state["model"] = model.to(_state["dev"]).eval()
    return _state["tok"], _state["model"], _state["dev"]


def predict_words(words):
    """Per-word label and confidence. Returns (labels, confs, truncated_windows)."""
    tok, model, dev = load_model()
    labels, confs, trunc = ["O"] * len(words), [0.0] * len(words), 0
    for a, b in make_windows(words, MAXW):
        chunk = words[a:b]
        enc = tok(chunk, is_split_into_words=True, truncation=True,
                  max_length=MAXLEN, return_tensors="pt")
        wids = enc.word_ids(0)
        with torch.no_grad():
            logits = model(**{k: v.to(dev) for k, v in enc.items()}).logits[0].float()
        probs = torch.softmax(logits, dim=-1).cpu()
        prev, seen = None, 0
        for k, w in enumerate(wids):
            if w is None or w == prev:
                prev = w
                continue
            prev, seen = w, w + 1
            p, i = probs[k].max(0)
            labels[a + w], confs[a + w] = NER_ID2TAG[int(i)], float(p)
        trunc += seen < len(chunk)
    for i, w in enumerate(words):
        if w == NL:
            labels[i], confs[i] = "O", 0.0
    return labels, confs, trunc


def _clean(t):
    return t.strip(" ,;:|-•·")


def get_spans(words, labels, confs):
    spans, cur = [], None
    for i, (w, l, c) in enumerate(zip(words, labels, confs)):
        if l == "O" or w == NL:
            cur = None
            continue
        typ = l[2:]
        if l.startswith("B-") or cur is None or cur["type"] != typ:
            cur = {"type": typ, "words": [w], "confs": [c], "start": i}
            spans.append(cur)
        else:
            cur["words"].append(w)
            cur["confs"].append(c)
    return [{"type": s["type"], "text": _clean(" ".join(s["words"])),
             "conf": sum(s["confs"]) / len(s["confs"]), "start": s["start"]} for s in spans]


def _best(spans, typ, near_top=False):
    c = [s for s in spans if s["type"] == typ and s["text"]]
    if near_top:
        top = [s for s in c if s["start"] < 40]
        c = top or c
    return max(c, key=lambda s: s["conf"]) if c else None


def _entry(value, conf, source, raw=None):
    return {"value": value, "confidence": float(conf), "source": source, "raw": raw}


def _empty():
    return _entry(None, 0.0, "none")


def _flat(s):
    return re.sub(r"[^a-z]", "", s.lower())


def _fallback_name(text):
    for line in text.splitlines():
        line = line.strip()
        if line:
            ws = line.split()
            if 1 <= len(ws) <= 4 and all(re.fullmatch(r"[A-Za-z.'\-]+", w) for w in ws):
                return line
            return None
    return None


def _nice_case(t):
    return t.title() if t.isupper() else t


def _split_location(text, all_texts=()):
    city, state = rules.split_location(text)
    if state is None:  # glued text like "AndhraPradesh"
        for t in [text] + list(all_texts):
            flat = _flat(t)
            for st in INDIAN_STATES:
                if _flat(st) in flat:
                    return city, st
    return city, state


# ---------- glued text and college / location choice ----------
_COLLEGE_KW = re.compile(
    r"(?i)\b(universit\w*|college|institute|technolog\w*|engineering|school|academy|"
    r"iit|iiit|nit|bits|vit|srm|vidyapeetham)\b")


def _unglue(text):
    """'VIT-APUniversity,Amaravati,AndhraPradesh' -> 'VIT-AP University,Amaravati,Andhra Pradesh'"""
    out = []
    for w in text.split():
        if len(w) >= 9:
            w = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", w)
            w = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", w)
        out.append(w)
    return " ".join(out)


def _split_college(text):
    """Returns (college_name, location_text_or_None). Splits at a comma only when
    what follows is clearly a place (a known state or city)."""
    t = _unglue(text)
    if "," in t:
        head, rest = t.split(",", 1)
        place = rules.lookup_state(rest) or any(c.lower() in rest.lower() for c, _ in CITIES)
        if head.strip() and place:
            return head.strip(), rest.strip(" ,")
    return t.strip(), None


def _pick_college(spans, degree_pos):
    best, best_score = None, -9.0
    for s in spans:
        if s["type"] != "COLLEGE" or not s["text"]:
            continue
        name, loc = _split_college(s["text"])
        score = s["conf"]
        if _COLLEGE_KW.search(name):
            score += 0.3
        if degree_pos is not None and abs(s["start"] - degree_pos) <= 30:
            score += 0.3
        if len(name) < 3 or (" " not in name and name.islower()):
            score -= 0.6
        if re.search(r"(?i)\bresume\b|\bcurriculum\b", name):
            score -= 1.0
        if score > best_score:
            best_score = score
            best = {"text": name, "conf": s["conf"], "start": s["start"],
                    "raw": s["text"], "loc": loc}
    return best


def _pick_location(spans, college):
    """Header location (candidate's own) beats a location next to the college."""
    cands = []
    if college and college["loc"]:
        cands.append((college["conf"] + 0.1, college["loc"], college["conf"]))
    for s in spans:
        if s["type"] != "LOCATION" or not s["text"]:
            continue
        header = s["start"] < 30
        near_top = s["start"] < 60
        near_col = college is not None and abs(s["start"] - college["start"]) <= 40
        if near_top or near_col:
            score = (s["conf"] + (0.3 if header else 0.0) + (0.1 if near_col else 0.0)
                     - s["start"] / 10000)
            cands.append((score, s["text"], s["conf"]))
    if not cands:
        return None
    cands.sort(key=lambda c: -c[0])
    return cands[0][1], cands[0][2]


def build_profile(text, spans):
    p = {f: _empty() for f in PROFILE_FIELDS}

    s = _best(spans, "NAME", near_top=True)
    if s:
        p["full_name"] = _entry(_nice_case(s["text"]), s["conf"], "ner", s["text"])
    else:
        fb = _fallback_name(text)
        if fb:
            p["full_name"] = _entry(_nice_case(fb), 0.5, "rule", fb)

    deg = _best(spans, "DEGREE")
    if deg:
        p["degree"] = _entry(rules.normalize_degree(deg["text"]) or deg["text"],
                             deg["conf"], "ner", deg["text"])
        br = _pick_branch(spans, deg["start"] if deg else None)
    if br:
        p["branch"] = _entry(rules.normalize_branch(br["text"]) or br["text"],
                             br["conf"], "ner", br["text"])

    col = _pick_college(spans, deg["start"] if deg else None)
    if col:
        p["college"] = _entry(col["text"], col["conf"], "ner", col["raw"])

    loc = _pick_location(spans, col)
    if loc:
        loc_text, loc_conf = loc
        city, state = _split_location(loc_text)
        if city and _is_state_fragment(city):
            city = None
        if state is None and col is not None:  # state split over lines: "Andhra" ... "Pradesh"
            near = [x["text"] for x in spans
                    if x["type"] == "LOCATION" and abs(x["start"] - col["start"]) <= 40]
            state = rules.lookup_state(" ".join(near))
        if city:
            p["city"] = _entry(city, loc_conf, "ner", loc_text)
        if state:
            p["state"] = _entry(state, loc_conf, "ner", loc_text)

    sk, seen, confs = [], set(), []
    for x in spans:
        t = x["text"]
        if x["type"] == "SKILL" and 2 <= len(t) <= 40 and t.lower() not in seen:
            seen.add(t.lower())
            sk.append(t)
            confs.append(x["conf"])
    if sk:
        p["skills"] = _entry(sk, sum(confs) / len(confs), "ner")

    for field, value in rules.extract_rule_fields(text).items():
        if value is not None:
            p[field] = _entry(value, 1.0, "rule")
    return p


def extract_all(text):
    """Returns (profile, spans, truncated_windows)."""
    words = text_to_words(_prep(text))
    if not words:
        return {f: _empty() for f in PROFILE_FIELDS}, [], 0
    labels, confs, trunc = predict_words(words)
    spans = get_spans(words, labels, confs)
    return build_profile(text, spans), spans, trunc


def extract_profile(text):
    return extract_all(text)[0]


def _load_text(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from src.pdf_text import extract_text
        return extract_text(path)
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: py -m src.extract "<resume.pdf | resume.txt>"')
        raise SystemExit(1)
    text = _load_text(sys.argv[1])
    t0 = time.time()
    profile, spans, trunc = extract_all(text)
    print(f"time: {time.time() - t0:.2f}s | words: {len(text_to_words(text))} | truncated windows: {trunc}\n")
    print(f"{'field':16}{'value':52}{'conf':>6}  source")
    for f in PROFILE_FIELDS:
        e = profile[f]
        v = e["value"]
        if isinstance(v, list):
            v = f"{len(v)} skills: " + ", ".join(v[:6]) + (" ..." if len(v) > 6 else "")
        v = "-" if v is None else str(v)
        print(f"{f:16}{v[:50]:52}{e['confidence']:6.2f}  {e['source']}")
    print("\nraw NER spans (type: text [conf] @word):")
    for typ in ["NAME", "COLLEGE", "DEGREE", "BRANCH", "LOCATION"]:
        for s in [x for x in spans if x["type"] == typ]:
            print(f"  {typ:9} {s['text']!r} [{s['conf']:.2f}] @{s['start']}")
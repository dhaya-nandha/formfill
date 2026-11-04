import json
import re
from pathlib import Path

from rapidfuzz import fuzz

from src import rules
from src.schema import BRANCH_ALIASES, DEGREE_ALIASES

_CFG = Path(__file__).resolve().parent.parent / "data" / "option_config.json"


def _load_tau():
    try:
        return float(json.load(open(_CFG))["tau_opt"])
    except Exception:
        return 85.0


TAU_OPT = _load_tau()
_SKIP = {"", "none", "choose", "select", "select one", "choose one", "other", "others"}
_WORD_NUM = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
             "one": 1, "two": 2, "three": 3, "four": 4}
_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}


def norm(s):
    s = str(s).lower().replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s)).strip()


def norm_skill(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#]+", " ", str(s).lower())).strip()


def parse_year(s):
    """'3rd Year', 'Third Year', 'III', 'Year 3', '3' -> 3. Ambiguous or unknown -> None."""
    toks = norm(s).split()
    found = set()
    for t in toks:
        if t in _WORD_NUM:
            found.add(_WORD_NUM[t])
        elif t in _ROMAN and len(toks) <= 3:
            found.add(_ROMAN[t])
        else:
            m = re.fullmatch(r"([1-6])(?:st|nd|rd|th)?", t)
            if m:
                found.add(int(m.group(1)))
    return found.pop() if len(found) == 1 else None


def _years(s):
    return re.findall(r"\b(?:19|20)\d{2}\b", str(s))


def _keys(text, aliases):
    padded = f" {norm(text)} "
    ntok = len(padded.split())
    found = set()
    for key, alist in aliases.items():
        for a in alist:
            na = norm(a)
            if not na or (len(na) <= 3 and ntok > 6):
                continue
            if f" {na} " in padded:
                found.add(key)
                break
    return found


def _acronym(s):
    words = [w for w in norm(s).split() if w not in ("of", "and", "the", "for")]
    return "".join(w[0] for w in words).upper()


def _score(field, value, option):
    nv, no = norm(value), norm(option)
    if not nv or not no:
        return 0.0
    if nv == no:
        return 100.0
    if field == "year_of_study":
        a, b = parse_year(value), parse_year(option)
        return 100.0 if (a is not None and a == b) else 0.0
    if field == "graduation_year":
        yv, yo = _years(value), _years(option)
        if not yv or not yo:
            return 0.0
        if yo == [yv[-1]]:
            return 100.0
        return 90.0 if (len(yo) > 1 and yo[-1] == yv[-1]) else 0.0
    if field == "degree":
        canon, ks = rules.normalize_degree(str(value)), _keys(option, DEGREE_ALIASES)
        if canon and ks:
            if canon not in ks:
                return 0.0
            return 100.0 if ks == {canon} else 90.0
    elif field == "branch":
        canon, ks = rules.normalize_branch(str(value)), _keys(option, BRANCH_ALIASES)
        if canon and ks:
            if canon not in ks:
                return 0.0
            return 95.0 if ks == {canon} else 88.0
    elif field == "college":
        flat = nv.replace(" ", "").upper()
        if len(flat) >= 3 and _acronym(option) == flat:
            return 95.0
    return float(fuzz.ratio(nv, no))


def _res(option, score, reason):
    return {"option": option, "score": float(score), "reason": reason}


def match_option(field, value, options, tau=None):
    """Pick the form option for a profile value. option=None means REVIEW."""
    tau = TAU_OPT if tau is None else tau
    if value is None or str(value).strip() == "":
        return _res(None, 0.0, "no profile value")
    cands = []
    for o in options:
        no = norm(o)
        if no in _SKIP or no.startswith("other"):
            continue
        cands.append((_score(field, value, o), o))
    if not cands:
        return _res(None, 0.0, "no usable options")
    cands.sort(key=lambda c: -c[0])
    best_s, best = cands[0]
    if best_s < tau:
        return _res(None, best_s, "no option is close enough")
    close = [c for c in cands if c[0] >= tau]
    if len(close) > 1 and best_s < 100:
        return _res(None, best_s, "several options fit: " + " / ".join(o for _, o in close[:3]))
    return _res(best, best_s, "ok")


def match_checkboxes(skills, options):
    """Select every option that equals a profile skill. Empty list means REVIEW."""
    sel = []
    for o in options:
        no = norm_skill(o)
        if norm(o) in _SKIP or norm(o).startswith("other"):
            continue
        for sk in skills or []:
            ns = norm_skill(sk)
            if ns == no or (len(ns) >= 4 and len(no) >= 4 and fuzz.ratio(ns, no) >= 92):
                sel.append(o)
                break
    return {"options": sel, "reason": "ok" if sel else "no profile skill matches the options"}
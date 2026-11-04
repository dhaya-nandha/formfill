import re

from src.schema import BRANCH_ALIASES, DEGREE_ALIASES, INDIAN_STATES


def _norm(s):
    s = str(s).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ---------- shared patterns ----------
_DEGREE_KW = re.compile(
    r"(?i)(?<![A-Za-z])(?:b\.?\s?tech|b\.\s?e(?![A-Za-z])|bca|b\.?\s?sc|m\.?\s?tech|mca|"
    r"m\.?\s?sc|mba|bachelors?|masters?|universit\w*|college|institute)(?![A-Za-z])")
_SCHOOL = re.compile(
    r"(?i)\b(?:10th|12th|tenth|twelfth|xii?|ssc|hsc|cbse|icse|class(?!\s+of)|school|"
    r"intermediate|secondary)\b")

# ---------- email ----------
_EMAIL = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")


def extract_email(text):
    m = _EMAIL.search(text or "")
    return m.group(0).strip(".").lower() if m else None


# ---------- phone (10-digit Indian mobile) ----------
_PHONE = re.compile(
    r"(?<![\d.])(?:\(?\+?91\)?[\s\-]*)?(?:0[\s\-]*)?"
    r"([6-9]\d{4}[\s\-]?\d{5}|[6-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{4})(?!\d)")


def extract_phone(text):
    m = _PHONE.search(text or "")
    return re.sub(r"\D", "", m.group(1)) if m else None


# ---------- CGPA ----------
_OUT_OF = re.compile(r"(?i)[(\[]?\s*(?:out\s+of|on\s+a\s+scale\s+of)\s+10(?:\.0+)?\s*[)\]]?")
_SEG_SPLIT = re.compile(r"\s*[|;•·]\s*|\s{3,}")
_LABEL_FIRST = re.compile(
    r"(?i)\b(?:cgpa|gpa|aggregate)\b[^0-9\n%]{0,15}?(\d{1,2}(?:\.\d{1,2})?)"
    r"(\s*/\s*(\d{1,2}(?:\.\d+)?))?(\s*%)?")
_NUM_FIRST = re.compile(
    r"(?i)(?<![\d./])(\d{1,2}(?:\.\d{1,2})?)(\s*/\s*(\d{1,2}(?:\.\d+)?))?(\s*%)?\s*"
    r"(?:cumulative\s+)?(?:cgpa|gpa|aggregate)\b")
_SLASH10 = re.compile(r"(?<![\d./])(\d{1,2}(?:\.\d{1,2})?)\s*/\s*10(?:\.0+)?(?![\d./])")


def _cgpa_ok(value, scale, pct):
    if pct:
        return None
    v = float(value)
    if scale is not None and abs(float(scale) - 10) > 1e-9:
        return None
    if not (0 < v <= 10):
        return None
    return round(v, 2)


def extract_cgpa(text):
    """Returns a float out of 10, or None. Percentages and other scales are rejected."""
    t = _OUT_OF.sub(" ", text or "")
    labelled, slash = [], []
    prev_school = False
    for line in t.splitlines():
        if not line.strip():
            continue
        for seg in _SEG_SPLIT.split(line):
            if not seg.strip():
                continue
            if _SCHOOL.search(seg) or (prev_school and not _DEGREE_KW.search(seg)):
                continue
            for pat in (_LABEL_FIRST, _NUM_FIRST):
                for m in pat.finditer(seg):
                    v = _cgpa_ok(m.group(1), m.group(3), m.group(4))
                    if v is not None:
                        labelled.append(v)
            for m in _SLASH10.finditer(seg):
                v = _cgpa_ok(m.group(1), None, None)
                if v is not None:
                    slash.append(v)
        prev_school = bool(_SCHOOL.search(line)) and not _DEGREE_KW.search(line)
    if labelled:
        return labelled[0]
    return slash[0] if slash else None


# ---------- links ----------
_GITHUB = re.compile(
    r"(?i)(?<![A-Za-z0-9.\-])(?:https?://)?(?:www\.)?github\.com/"
    r"([A-Za-z0-9][A-Za-z0-9\-]{0,38})(?![A-Za-z0-9\-])")
_LINKEDIN = re.compile(
    r"(?i)(?<![A-Za-z0-9.\-])(?:https?://)?(?:(?:www|[a-z]{2,3})\.)?linkedin\.com/in/"
    r"([A-Za-z0-9\-_%]+)")


def extract_github(text):
    m = _GITHUB.search(text or "")
    return f"https://github.com/{m.group(1)}" if m else None


def extract_linkedin(text):
    m = _LINKEDIN.search(text or "")
    return f"https://www.linkedin.com/in/{m.group(1)}" if m else None


# ---------- graduation year ----------
_MONTH = r"(?:[A-Za-z]{3,9}\.?\s+)?"
_RANGE = re.compile(
    r"(?<!\d)(?:\d{1,2}/)?((?:19|20)\d{2})\s*(?:-|–|—|to)\s*" + _MONTH +
    r"(?:\d{1,2}/)?((?:19|20)\d{2})(?!\d)", re.I)
_RANGE_SHORT = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*[-–—]\s*(\d{2})(?!\d)")
_SINGLE = re.compile(
    r"(?i)\b(?:expected|graduat\w*|pass(?:ing)?[\s\-]*out|passing|batch|class\s+of)\b"
    r"[^0-9\n]{0,25}((?:19|20)\d{2})")
_EDU_HEADER = re.compile(
    r"(?i)^\W*(?:education(?:al)?(?:\s+(?:details|background|qualifications?))?|"
    r"academic(?:\s+(?:details|qualifications?|background|profile))?|qualifications?)\W*$")
_STOP_HEADER = re.compile(
    r"(?i)^\W*(?:work\s+)?(?:experience|projects?|skills|technical\s+skills|certifications?|"
    r"achievements?|internships?|positions?\s+of\s+responsibility|extra[\s\-]?curricular\w*|"
    r"summary|objective|interests|publications|awards)\W*$")


def _education_lines(text):
    lines = (text or "").splitlines()
    block, i = [], 0
    while i < len(lines):
        if _EDU_HEADER.match(lines[i]):
            j = i + 1
            while j < len(lines) and j - i <= 20 and not _STOP_HEADER.match(lines[j]):
                block.append(lines[j])
                j += 1
            i = j
        else:
            i += 1
    if block:
        return block
    return [l for l in lines if _DEGREE_KW.search(l)]


_DEGREE_ONLY = re.compile(
    r"(?i)(?<![A-Za-z])(?:b\.?\s?tech|b\.\s?e(?![A-Za-z])|bca|b\.?\s?sc|m\.?\s?tech|mca|"
    r"m\.?\s?sc|mba|bachelors?|masters?)(?![A-Za-z])")


def extract_graduation_year(text):
    """Latest year in the education part of the resume, as a string, or None."""
    lines = _education_lines(text)
    cands = []
    for i, line in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        school_here = _SCHOOL.search(line) and not _DEGREE_ONLY.search(line)
        school_next = (_SCHOOL.search(nxt) and not _DEGREE_ONLY.search(nxt)
                       and not _RANGE.search(nxt) and not _RANGE_SHORT.search(nxt))
        if school_here or school_next:
            continue
        for m in _RANGE.finditer(line):
            s, e = int(m.group(1)), int(m.group(2))
            if s <= e:
                cands.append(e)
        for m in _RANGE_SHORT.finditer(line):
            s = int(m.group(1))
            e = (s // 100) * 100 + int(m.group(2))
            if s <= e:
                cands.append(e)
        for m in _SINGLE.finditer(line):
            cands.append(int(m.group(1)))
    cands = [y for y in cands if 2000 <= y <= 2045]
    return str(max(cands)) if cands else None


# ---------- branch / degree / state lookups ----------
def _match_alias(text, aliases):
    nt = _norm(text)
    if not nt:
        return None
    padded = f" {nt} "
    ntokens = len(nt.split())
    best = None
    for key, alist in aliases.items():
        for a in alist:
            na = _norm(a)
            if not na:
                continue
            if len(na) <= 3 and ntokens > 6:
                continue  # short aliases like "it" only count in short texts
            if f" {na} " in padded:
                if best is None or len(na) > best[0]:
                    best = (len(na), key)
    return best[1] if best else None


def normalize_branch(text):
    return _match_alias(text, BRANCH_ALIASES)


def normalize_degree(text):
    return _match_alias(text, DEGREE_ALIASES)


_STATE_NORMS = {_norm(s): s for s in INDIAN_STATES}


def lookup_state(text):
    padded = f" {_norm(text)} "
    found = []
    for ns, name in _STATE_NORMS.items():
        pos = padded.find(f" {ns} ")
        if pos >= 0:
            found.append((pos, -len(ns), name))
    return min(found)[2] if found else None


def split_location(text):
    """'Amaravati, Andhra Pradesh' -> ('Amaravati', 'Andhra Pradesh')."""
    if not text or not text.strip():
        return None, None
    state = lookup_state(text)
    city = None
    for part in re.split(r"[,|/;]", text):
        part = part.strip()
        n = _norm(part)
        if part and n not in _STATE_NORMS and n not in ("india", "bharat"):
            city = part
            break
    return city, state


# ---------- all rule-based fields at once ----------
def extract_rule_fields(text):
    return {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "cgpa": extract_cgpa(text),
        "github": extract_github(text),
        "linkedin": extract_linkedin(text),
        "graduation_year": extract_graduation_year(text),
    }


if __name__ == "__main__":
    sample = """Asha Rao
Email: asha.rao@gmail.com | +91 98765 43210
github.com/asha-rao | linkedin.com/in/asha-rao-123/
EDUCATION
ABC Public School (CBSE), 2021 - 2023   Percentage: 92%
XYZ University, B.Tech CSE   2023 - 2027
CGPA: 8.4/10
PROJECTS
Chat app 2025 - 2026"""
    for k, v in extract_rule_fields(sample).items():
        print(f"{k:16} {v}")
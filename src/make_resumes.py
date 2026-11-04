import json
import random
import sys
from collections import Counter
from pathlib import Path

from src import rules
from src.schema import NER_TAGS
from src.vocab_people_places import CITIES, COLLEGES, FIRST_NAMES, SURNAMES
from src.vocab_resume import (BRANCHES, CLUBS, COMPANIES, DEGREES, PROJECT_BULLET_TEMPLATES,
                              PROJECT_TITLES, ROLE_TITLES, SCHOOLS, SKILL_CATEGORY_LABELS,
                              SKILLS, VALID_COMBOS)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "resumes_synth"
SEED = 42
COUNTS = {"train": 3000, "dev": 300, "test": 300}
OFFSET = {"train": 0, "dev": 1000, "test": 2000}

DEG_W = {"B.Tech": 0.45, "B.E.": 0.15, "BCA": 0.15, "B.Sc": 0.05, "M.Tech": 0.10, "MCA": 0.10}
DUR = {"B.Tech": 4, "B.E.": 4, "BCA": 3, "B.Sc": 3, "M.Tech": 2, "MCA": 2}
EDU_HDRS = ["Education", "Academic Details", "Qualifications", "Educational Qualifications",
            "Academic Background"]
SKILL_HDRS = ["Skills", "Technical Skills"]
EXP_HDRS = ["Experience", "Work Experience", "Internships", "Positions of Responsibility"]


def split_list(items, seed):
    items = list(items)
    random.Random(seed).shuffle(items)
    a, b = int(len(items) * 0.8), int(len(items) * 0.9)
    return {"train": items[:a], "dev": items[a:b], "test": items[b:]}


_VOCAB = {"first": FIRST_NAMES, "sur": SURNAMES, "college": COLLEGES, "company": COMPANIES,
          "school": SCHOOLS, "project": PROJECT_TITLES}
POOLS = {k: split_list(v, SEED + i) for i, (k, v) in enumerate(_VOCAB.items())}


def S(text, tag=None):
    return (text, tag)


def chunks(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def join_items(items, sep):
    out = []
    for i, it in enumerate(items):
        if i:
            out.append(sep)
        out.extend(it)
    return out


def interleave(left, right):
    return [(left[i] if i < len(left) else []) + (right[i] if i < len(right) else [])
            for i in range(max(len(left), len(right)))]


# ---------------- tokens ----------------
def to_tokens(lines):
    tokens, labels, line_starts = [], [], []
    for line in lines:
        started = False
        for text, tag in line:
            for i, w in enumerate(text.split()):
                if not started:
                    line_starts.append(len(tokens))
                    started = True
                tokens.append(w)
                labels.append("O" if tag is None else ("B-" if i == 0 else "I-") + tag)
    return tokens, labels, line_starts


def render(tokens, line_starts):
    starts = set(line_starts)
    out = []
    for i, t in enumerate(tokens):
        if i > 0:
            out.append("\n" if i in starts else " ")
        out.append(t)
    return "".join(out)


# ---------------- person ----------------
MON_S = ["Aug", "Aug", "Jul", "Sep", "Jun", "August", "July"]
MON_E = ["May", "Jun", "Apr", "May", "June", "May"]


def make_dates(rng, s, e):
    kind = rng.choice(["plain", "plain", "en", "en_sp", "month", "short", "slash",
                       "expected", "expected_m", "batch"])
    if kind == "plain":
        return f"{s} - {e}"
    if kind == "en":
        return f"{s}–{e}"
    if kind == "en_sp":
        return f"{s} – {e}"
    if kind == "month":
        return f"{rng.choice(MON_S)} {s} – {rng.choice(MON_E)} {e}"
    if kind == "short":
        return f"{s}-{str(e)[2:]}"
    if kind == "slash":
        return f"{rng.randint(6, 9):02d}/{s} - {rng.randint(4, 6):02d}/{e}"
    if kind == "expected":
        return f"Expected {e}"
    if kind == "expected_m":
        return f"Expected {rng.choice(MON_E)} {e}"
    return rng.choice(["Batch of", "Class of"]) + f" {e}"


def make_person(rng, split):
    first = rng.choice(POOLS["first"][split])
    sur = rng.choice(POOLS["sur"][split])
    mid = rng.choice("ABCDEGHKMNPRSTV")
    r = rng.random()
    if r < 0.55:
        name_txt = f"{first} {sur}"
    elif r < 0.75:
        name_txt = f"{first} {mid}. {sur}"
    elif r < 0.90:
        name_txt = f"{first} {sur}".upper()
    else:
        name_txt = f"{sur} {first}"
    h1, h2 = first.lower(), sur.lower()
    email = rng.choice([f"{h1}.{h2}", f"{h1}{h2}", f"{h1}{h2}{rng.randint(1, 99)}",
                        f"{h1[0]}{h2}", f"{h1}_{h2}"]) + "@" + rng.choice(
        ["gmail.com", "gmail.com", "gmail.com", "outlook.com", "yahoo.com", "student.edu.in"])
    digits = str(rng.randint(6, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(9))
    phone_txt = rng.choice(["+91 {a} {b}", "{a}-{b}", "+91-{d}", "{d}", "(+91) {a} {b}",
                            "+91 {d}", "+91{d}"]).format(a=digits[:5], b=digits[5:], d=digits)

    deg = rng.choices(list(DEG_W), weights=list(DEG_W.values()))[0]
    branch_key = rng.choice(VALID_COMBOS[deg])
    if branch_key is None:
        b_canon, b_txt = None, None
    elif branch_key in BRANCHES:
        b_canon, b_txt = branch_key, rng.choice(BRANCHES[branch_key])
    else:
        b_canon, b_txt = branch_key, branch_key
    degree_txt = rng.choice(DEGREES[deg])
    grad = rng.randint(2025, 2029)
    start = grad - DUR[deg]

    college = rng.choice(POOLS["college"][split])
    r = rng.random()
    if r < 0.55:
        college_txt = college[0]
        if rng.random() < 0.08:
            college_txt = college_txt.replace(" ", "")
    elif r < 0.80:
        college_txt = college[1]
    elif r < 0.90:
        college_txt = college[0].upper()
    else:
        college_txt = college[0].lower()

    city, state = rng.choice(CITIES)
    loc_mode = rng.choices(["header", "edu", "none"], weights=[0.45, 0.40, 0.15])[0]
    v = rng.choice(["both", "both", "both_india", "city_only", "glued"])
    loc_has_state = v != "city_only"
    loc_txt = {"both": f"{city}, {state}", "both_india": f"{city}, {state}, India",
               "city_only": city,
               "glued": f"{city},{state.replace(' ', '')}"}[v]

    has_cgpa = rng.random() < 0.9
    cgpa = round(rng.uniform(6.0, 9.9), rng.choice([1, 2])) if has_cgpa else None
    cgpa_txt = None
    if has_cgpa:
        lab = rng.choice(["CGPA", "CGPA", "GPA", "Aggregate", "Cumulative GPA"])
        val = rng.choice([f"{cgpa}", f"{cgpa}/10", f"{cgpa} / 10"])
        cgpa_txt = rng.choice([f"{lab}: {val}", f"{lab}: {val}", f"{lab} - {val}",
                               f"{val} {lab}", f"{lab}:{cgpa}"])
    decoy = None
    if not has_cgpa and rng.random() < 0.5:
        decoy = [S(f"{rng.choice(['Percentage', 'Aggregate'])}: {rng.randint(60, 95)}%")]

    gh_handle = rng.choice([f"{h1}-{h2}", f"{h1}{h2}", f"{h1[0]}{h2}", f"{h1}{rng.randint(1, 99)}"])
    li_slug = f"{h1}-{h2}-" + "".join(rng.choice("0123456789abcdef") for _ in range(8))
    gh_url = f"https://github.com/{gh_handle}"
    li_url = f"https://www.linkedin.com/in/{li_slug}"
    return {
        "first": first, "sur": sur, "name_txt": name_txt, "email": email, "digits": digits,
        "phone_txt": phone_txt, "deg": deg, "degree_txt": degree_txt, "b_canon": b_canon,
        "b_txt": b_txt, "grad": grad, "start": start, "college": college,
        "college_txt": college_txt, "city": city, "state": state, "loc_mode": loc_mode,
        "loc_txt": loc_txt, "loc_has_state": loc_has_state, "cgpa": cgpa, "cgpa_txt": cgpa_txt,
        "decoy": decoy, "dates": make_dates(rng, start, grad),
        "has_gh": rng.random() < 0.7, "has_li": rng.random() < 0.7,
        "gh_url": gh_url, "li_url": li_url,
        "gh_txt": rng.choice([f"github.com/{gh_handle}", gh_url, f"GitHub: github.com/{gh_handle}",
                              f"www.github.com/{gh_handle}"]),
        "li_txt": rng.choice([f"linkedin.com/in/{li_slug}", li_url,
                              f"LinkedIn: linkedin.com/in/{li_slug}",
                              f"linkedin.com/in/{li_slug}/"]),
        "skills": rng.sample(SKILLS, rng.randint(6, 18)),
    }


# ---------------- blocks ----------------
def hdr(p, text):
    s = p["hdr_style"]
    if s == "upper":
        text = text.upper()
    elif s == "colon":
        text = text + ":"
    lines = [[S(text)]]
    if s == "underline":
        lines.append([S("-" * len(text))])
    return lines


def header_lines(rng, p):
    items = [[S(rng.choice(["{}", "{}", "Phone: {}", "Mobile: {}", "Ph: {}"]).format(p["phone_txt"]))],
             [S(rng.choice(["{}", "{}", "Email: {}", "E-mail: {}"]).format(p["email"]))]]
    if p["loc_mode"] == "header":
        pre = rng.choice(["", "", "Location:", "Address:"])
        items.append(([S(pre)] if pre else []) + [S(p["loc_txt"], "LOCATION")])
    tail = []
    if p["has_gh"] or p["has_li"]:
        if rng.random() < 0.75:
            if p["has_gh"]:
                items.append([S(p["gh_txt"])])
            if p["has_li"]:
                items.append([S(p["li_txt"])])
        else:
            if p["has_li"]:
                items.append([S("LinkedIn")])
                tail.append([S(p["li_url"])])
            if p["has_gh"]:
                items.append([S("GitHub")])
                tail.append([S(p["gh_url"])])
    rng.shuffle(items)
    sep = S(rng.choice(["|", "•", "·", "|"]))
    name = [S(p["name_txt"], "NAME")]
    style = rng.choice(["one_line", "two_lines", "stacked"])
    if style == "one_line":
        lines = [name, join_items(items, sep)]
    elif style == "two_lines":
        k = max(1, len(items) // 2)
        lines = [name, join_items(items[:k], sep), join_items(items[k:], sep)]
    else:
        lines = [name] + items
    return lines, tail


def school_lines(rng, p, split):
    lines = []
    e = p["start"]
    for label_opts, (y1, y2), prob in [(["Class XII", "12th", "Class XII (CBSE)"], (e - 2, e), 0.7),
                                       (["Class X", "10th", "Class X (SSC)"], (e - 4, e - 2), 0.6)]:
        if rng.random() > prob:
            continue
        sch = rng.choice(POOLS["school"][split])
        lab = rng.choice(label_opts)
        pct = rng.randint(60, 98)
        if rng.random() < 0.5:
            last = (S(f"{lab} CGPA: {round(rng.uniform(7, 9.9), 1)}") if rng.random() < 0.15
                    else S(f"{rng.choice(['Percentage', 'Marks'])}: {pct}%"))
            lines.append([S(sch), S("|"), S(lab), S("|"), S(f"{y1} - {y2}"), S("|"), last])
        else:
            lines.append([S(f"{lab}: {pct}%"), S("|"), S(sch), S("|"), S(f"{y1} - {y2}")])
    return lines


def edu_lines(rng, p, fmt):
    d = S(p["degree_txt"], "DEGREE")
    b = S(p["b_txt"], "BRANCH") if p["b_txt"] else None
    loc = S(p["loc_txt"], "LOCATION") if p["loc_mode"] == "edu" else None
    c = S(p["college_txt"] + ("," if loc else ""), "COLLEGE")
    dates = S(p["dates"])
    cg = [S(p["cgpa_txt"])] if p["cgpa"] is not None else None
    college_line = [c] + ([loc] if loc else [])
    if fmt == 1:
        lines = [[d] + ([S("in"), b] if b else []) + [dates], college_line]
        if cg:
            lines.append(cg)
    elif fmt == 2:
        lines = [college_line, [d] + ([S("-"), b] if b else []) + [S("|"), dates]]
        if cg:
            lines.append(cg)
    elif fmt == 3:
        parts = [[d]] + ([[b]] if b else []) + [college_line, [dates]] + ([cg] if cg else [])
        lines = [join_items(parts, S("|"))]
    elif fmt == 4:
        lines = [[d] + ([b] if b else []) + [dates], college_line]
        if cg:
            lines.append(cg)
    else:
        lines = [[d]]
        if b:
            lines.append([S(rng.choice(["Specialization:", "Branch:", "Major:"])), b])
        lines += [college_line, [dates]]
        if cg:
            lines.append(cg)
    if p["decoy"]:
        lines.append(p["decoy"])
    return lines + p["school_lines"]


def skill_segs(chunk, sep=None):
    segs = []
    for i, sk in enumerate(chunk):
        if sep is None:
            segs.append(S(sk + ("" if i == len(chunk) - 1 else ","), "SKILL"))
        else:
            if i:
                segs.append(S(sep))
            segs.append(S(sk, "SKILL"))
    return segs


def skills_lines(rng, p):
    sk = p["skills"]
    style = rng.choice(["comma", "comma", "categorized", "bullets", "pipe", "dot"])
    if style == "comma":
        lines = []
        for k, ch in enumerate(chunks(sk, rng.choice([6, 8, 12, 20]))):
            segs = skill_segs(ch)
            if k == 0 and rng.random() < 0.4:
                segs = [S(rng.choice(["Skills:", "Technologies:", "Tech Stack:"]))] + segs
            lines.append(segs)
        return lines
    if style == "categorized":
        k = min(rng.randint(2, 4), len(sk))
        cats = rng.sample(SKILL_CATEGORY_LABELS, k)
        per = (len(sk) + k - 1) // k
        return [[S(cat + ":")] + skill_segs(ch) for cat, ch in zip(cats, chunks(sk, per))]
    if style == "bullets":
        return [[S(p["bullet"]), S(s, "SKILL")] for s in sk]
    sep = "|" if style == "pipe" else "·"
    return [skill_segs(ch, sep) for ch in chunks(sk, 6)]


def fill(rng, tmpl, kind):
    return tmpl.format(kind=kind, skill=rng.choice(SKILLS), skill2=rng.choice(SKILLS),
                       n=rng.randint(10, 95), t=rng.randint(2, 6))


def project_lines(rng, p, split):
    lines = []
    for _ in range(rng.randint(1, 3)):
        title = rng.choice(POOLS["project"][split])
        yr = rng.randint(2023, 2026)
        lines.append([S(title), S(str(yr) if rng.random() < 0.7 else f"{yr - 1} - {yr}")])
        lines.append([S("Tech: " + ", ".join(rng.sample(SKILLS, rng.randint(2, 5))))])
        for _ in range(rng.randint(1, 3)):
            lines.append([S(p["bullet"]), S(fill(rng, rng.choice(PROJECT_BULLET_TEMPLATES), title))])
    return lines


def experience_lines(rng, p, split):
    lines = []
    for _ in range(rng.randint(1, 2)):
        role = rng.choice(ROLE_TITLES)
        r = rng.random()
        if r < 0.55:
            org = rng.choice(POOLS["company"][split])
        elif r < 0.85:
            org = rng.choice(CLUBS)
        else:
            org = rng.choice(POOLS["college"][split])[0]  # another college, always O
        y = rng.randint(2023, 2026)
        dates = f"{y} - Present" if rng.random() < 0.3 else f"{y} - {y + 1}"
        row = [S(role), S("|"), S(org)]
        if rng.random() < 0.5:
            row += [S("|"), S(rng.choice(CITIES)[0])]
        row += [S("|"), S(dates)]
        lines.append(row)
        lines.append([S(p["bullet"]), S(fill(rng, rng.choice(PROJECT_BULLET_TEMPLATES), role))])
    return lines


# ---------------- one resume ----------------
def make_resume(rng, split, idx):
    p = make_person(rng, split)
    p["hdr_style"] = rng.choice(["title", "title", "upper", "colon", "underline"])
    p["bullet"] = rng.choice(["•", "-", "*", "▪"])
    p["school_lines"] = school_lines(rng, p, split)
    fmt = rng.randint(1, 5)
    twocol = rng.random() < 0.12
    has_skills = rng.random() < 0.92

    head, tail = header_lines(rng, p)
    edu_body = edu_lines(rng, p, fmt)
    skill_body = skills_lines(rng, p) if has_skills else []
    edu_hdr = hdr(p, rng.choice(EDU_HDRS))

    sections, layout = {}, f"edu{fmt}"
    if twocol and has_skills:
        right = hdr(p, rng.choice(SKILL_HDRS))[:1] + skill_body
        sections["edu"] = edu_hdr + interleave(edu_body, right)
        layout = "twocol"
    else:
        sections["edu"] = edu_hdr + edu_body
        if has_skills:
            sections["skills"] = hdr(p, rng.choice(SKILL_HDRS)) + skill_body
    if rng.random() < 0.8:
        sections["projects"] = hdr(p, "Projects") + project_lines(rng, p, split)
    if rng.random() < 0.5:
        sections["exp"] = hdr(p, rng.choice(EXP_HDRS)) + experience_lines(rng, p, split)
    order = [k for k in ("edu", "skills", "projects", "exp") if k in sections]
    if rng.random() > 0.65:
        rng.shuffle(order)

    lines = head + [ln for k in order for ln in sections[k]] + tail
    tokens, labels, line_starts = to_tokens(lines)
    has_loc = p["loc_mode"] != "none"
    gold = {
        "full_name": f"{p['first']} {p['sur']}", "email": p["email"], "phone": p["digits"],
        "college": p["college"][0], "degree": p["deg"], "branch": p["b_canon"],
        "year_of_study": None, "graduation_year": str(p["grad"]), "cgpa": p["cgpa"],
        "city": p["city"] if has_loc else None,
        "state": p["state"] if (has_loc and p["loc_has_state"]) else None,
        "github": p["gh_url"] if p["has_gh"] else None,
        "linkedin": p["li_url"] if p["has_li"] else None,
        "skills": p["skills"] if has_skills else [], "target_role": None,
        "college_short": p["college"][1],
    }
    return {"id": f"{split}_{idx:05d}", "layout": layout, "text": render(tokens, line_starts),
            "tokens": tokens, "labels": labels, "line_starts": line_starts, "gold": gold}


# ---------------- checks ----------------
def validate(rec):
    errs = []
    if len(rec["tokens"]) != len(rec["labels"]):
        errs.append("length mismatch")
    prev = "O"
    for i, lab in enumerate(rec["labels"]):
        if lab not in NER_TAGS:
            errs.append(f"bad tag {lab}")
        if lab.startswith("I-") and (prev == "O" or prev[2:] != lab[2:]):
            errs.append(f"orphan {lab} at {i}")
        prev = lab
    return errs


def spans(rec):
    out, cur = {}, None
    for tok, lab in zip(rec["tokens"], rec["labels"]):
        if lab.startswith("B-"):
            cur = [tok]
            out.setdefault(lab[2:], []).append(cur)
        elif lab.startswith("I-") and cur is not None:
            cur.append(tok)
        else:
            cur = None
    return {k: [" ".join(v) for v in vs] for k, vs in out.items()}


def tagged(rec):
    toks, labs, starts = rec["tokens"], rec["labels"], set(rec["line_starts"])
    out, i = [], 0
    while i < len(toks):
        if i > 0:
            out.append("\n" if i in starts else " ")
        if labs[i].startswith("B-"):
            typ = labs[i][2:]
            j = i + 1
            while j < len(toks) and labs[j] == "I-" + typ and j not in starts:
                j += 1
            out.append(f"[{typ}: {' '.join(toks[i:j])}]")
            i = j
        else:
            out.append(toks[i])
            i += 1
    return "".join(out)


def check_rules(recs, show=3):
    fields = ["email", "phone", "cgpa", "github", "linkedin", "graduation_year"]
    ok, bad = Counter(), []
    for rec in recs:
        pred = rules.extract_rule_fields(rec["text"])
        for f in fields:
            g, q = rec["gold"][f], pred[f]
            same = (g is None and q is None) or (g is not None and q is not None and
                                                 (abs(g - q) < 1e-9 if f == "cgpa" else g == q))
            if same:
                ok[f] += 1
            else:
                bad.append((rec["id"], f, g, q))
    print(f"  {'rule field':16}{'correct':>10}{'accuracy':>10}")
    for f in fields:
        print(f"  {f:16}{ok[f]:>5}/{len(recs):<4}{ok[f] / len(recs):>9.3f}")
    for b in bad[:show]:
        print(f"    mismatch {b[0]} {b[1]}: gold={b[2]!r} rules={b[3]!r}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if cmd == "preview":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        rng = random.Random(SEED + 7)
        for i in range(n):
            rec = make_resume(rng, "train", i)
            print(f"\n===== {rec['id']} | layout {rec['layout']} | {len(rec['tokens'])} words =====")
            print(tagged(rec))
            g = {k: v for k, v in rec["gold"].items() if k != "skills"}
            print("\ngold:", g, "| skills:", len(rec["gold"]["skills"]))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for split, n in COUNTS.items():
        rng = random.Random(SEED + OFFSET[split])
        recs = [make_resume(rng, split, i) for i in range(n)]
        with open(OUT / f"{split}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        data[split] = recs
    for split, recs in data.items():
        print(f"\n=== {split}: {len(recs)} resumes, avg {sum(len(r['tokens']) for r in recs) / len(recs):.0f} words ===")
        print("  layouts:", dict(Counter(r["layout"] for r in recs)))
        ent = Counter()
        for r in recs:
            ent.update(l[2:] for l in r["labels"] if l.startswith("B-"))
        print("  entities (B- count):", dict(ent))
        errs = [(r["id"], e) for r in recs for e in validate(r)]
        print("  label validation errors:", len(errs), errs[:3])
        missing = []
        for r in recs:
            sp, g = spans(r), r["gold"]
            for need, cond in [("NAME", True), ("COLLEGE", True), ("DEGREE", True),
                               ("BRANCH", g["branch"] is not None),
                               ("LOCATION", g["city"] is not None),
                               ("SKILL", bool(g["skills"]))]:
                if cond and need not in sp:
                    missing.append((r["id"], need))
        print("  resumes missing an expected entity:", len(missing), missing[:3])
        check_rules(recs)
    tr = {r["gold"]["college"] for r in data["train"]}
    tn = {r["gold"]["full_name"] for r in data["train"]}
    for s in ("dev", "test"):
        print(f"\noverlap with train ({s}): colleges {len({r['gold']['college'] for r in data[s]} & tr)},"
              f" full names {len({r['gold']['full_name'] for r in data[s]} & tn)}")
    print("\nSaved to data/resumes_synth/{train,dev,test}.jsonl")


if __name__ == "__main__":
    main()
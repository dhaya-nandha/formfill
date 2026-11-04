import json
import re
from urllib.parse import urlencode, urlsplit, urlunsplit

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TYPE_NAMES = {0: "short_text", 1: "paragraph", 2: "multiple_choice", 3: "dropdown",
              4: "checkboxes", 5: "linear_scale", 7: "grid", 9: "date", 10: "time",
              13: "file_upload"}


class FormError(Exception):
    pass


class SignInRequired(FormError):
    pass


def _clean(t):
    return " ".join(str(t).split())


def fetch_form_page(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                         timeout=30, allow_redirects=True)
    except requests.RequestException as e:
        raise FormError(f"could not open the link: {e}")
    if "accounts.google.com" in r.url:
        raise SignInRequired("This form needs Google sign-in. Open it in a form that allows "
                             "anyone with the link (no sign-in), or paste the questions manually.")
    if r.status_code != 200:
        raise FormError(f"the link returned HTTP {r.status_code}")
    return r.url, r.text


def parse_html(html):
    m = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);\s*</script>", html, re.S)
    if not m:
        raise FormError("form data not found (not a Google Form, or it needs sign-in)")
    data = json.loads(m.group(1))
    items = (data[1][1] if len(data) > 1 and data[1] else None) or []
    questions = []
    for item in items:
        try:
            title, code, subs = _clean(item[1] or ""), item[3], item[4]
        except (IndexError, TypeError):
            continue
        if not subs:
            continue
        for sub in subs:
            try:
                entry = sub[0]
                raw_opts = sub[1] or []
                required = bool(sub[2]) if len(sub) > 2 else False
            except (IndexError, TypeError):
                continue
            q = title
            if code == 7:
                try:
                    q = f"{title} - {_clean(sub[3][0])}"
                except (IndexError, TypeError):
                    pass
            options = [_clean(o[0]) for o in raw_opts
                       if isinstance(o, list) and o and isinstance(o[0], str) and o[0].strip()]
            questions.append({"entry_id": f"entry.{entry}", "question": q,
                              "type": TYPE_NAMES.get(code, f"type_{code}"),
                              "options": options, "required": required})
    name = data[3] if len(data) > 3 and isinstance(data[3], str) else ""
    return {"name": name, "questions": questions}


def parse_form(url):
    final_url, html = fetch_form_page(url)
    form = parse_html(html)
    form["url"] = final_url
    return form


def load_form_json(path):
    """Old test forms (form_00.json ...) use the same question format."""
    data = json.load(open(path, encoding="utf-8"))
    return {"name": data.get("name", ""), "questions": data["questions"],
            "expected": data.get("expected"), "url": None}


def build_prefill_link(form_url, answers):
    """answers: {'entry.123': 'text' | ['opt1', 'opt2']}. Checkbox keys repeat."""
    parts = urlsplit(form_url)
    path = parts.path if "/viewform" in parts.path else parts.path.rstrip("/") + "/viewform"
    pairs = [("usp", "pp_url")]
    for key, val in answers.items():
        for v in (val if isinstance(val, list) else [val]):
            if v is not None and str(v) != "":
                pairs.append((key, str(v)))
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(pairs), ""))

def parse_form_browser(url, timeout=90):
    """Fallback: load the page in a real browser (separate process), then parse the same way."""
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent.parent / "tools" / "parse_form.py"
    try:
        r = subprocess.run([sys.executable, str(script), url], capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        raise FormError("the browser fallback timed out")
    try:
        data = json.loads(r.stdout)
    except ValueError:
        raise FormError("the browser fallback failed: " + (r.stderr.strip()[-200:] or "no output"))
    if "error" in data:
        raise FormError("the browser fallback failed: " + data["error"])
    if "accounts.google.com" in data["url"]:
        raise SignInRequired("This form needs Google sign-in. Use a form that allows anyone "
                             "with the link, or paste the questions manually.")
    form = parse_html(data["html"])
    form["url"] = data["url"]
    return form
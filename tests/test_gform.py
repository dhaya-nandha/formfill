import json

from src.gform import build_prefill_link, parse_html


def _html(items):
    data = [None, [None, items], None, "My Form"]
    return f"<script>var FB_PUBLIC_LOAD_DATA_ = {json.dumps(data)};</script>"


def test_parse_basic():
    items = [
        [1, "  Full   Name ", None, 0, [[111, None, 1]]],
        [2, "Year", None, 2, [[222, [["1st Year"], ["2nd Year"], ["", None, None, None, 1]], 0]]],
        [3, "Image only", None, 11, None],
    ]
    form = parse_html(_html(items))
    qs = form["questions"]
    assert len(qs) == 2
    assert qs[0]["entry_id"] == "entry.111" and qs[0]["question"] == "Full Name"
    assert qs[0]["type"] == "short_text" and qs[0]["required"] is True
    assert qs[1]["options"] == ["1st Year", "2nd Year"] and qs[1]["type"] == "multiple_choice"
    assert form["name"] == "My Form"


def test_prefill():
    link = build_prefill_link("https://docs.google.com/forms/d/e/ABC/viewform?usp=sf_link",
                              {"entry.1": "A B", "entry.2": ["x", "y"], "entry.3": None})
    assert link.startswith("https://docs.google.com/forms/d/e/ABC/viewform?usp=pp_url")
    assert "entry.1=A+B" in link
    assert link.count("entry.2=") == 2
    assert "entry.3" not in link
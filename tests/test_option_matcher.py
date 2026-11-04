import pytest

from src.option_matcher import match_checkboxes, match_option, parse_year


@pytest.mark.parametrize("text,expected", [
    ("3rd Year", 3), ("Third Year", 3), ("III", 3), ("Year 3", 3), ("3", 3),
    ("II Year", 2), ("1st and 2nd year", None), ("Final Year", None), ("2023 - 2027", None),
])
def test_parse_year(text, expected):
    assert parse_year(text) == expected


Y4 = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
CASES = [
    ("year_of_study", "3rd Year", Y4, "3rd Year"),
    ("year_of_study", "3", ["First Year", "Second Year", "Third Year", "Fourth Year"], "Third Year"),
    ("year_of_study", "3rd Year", ["I", "II", "III", "IV"], "III"),
    ("year_of_study", "2", ["1st and 2nd year", "3rd year"], None),
    ("degree", "B.Tech", ["BTech", "M.Tech", "MCA"], "BTech"),
    ("degree", "B.Tech", ["B.E.", "BCA", "MCA"], None),
    ("degree", "B.Tech", ["Bachelor of Technology", "Bachelor of Science"], "Bachelor of Technology"),
    ("degree", "B.Tech", ["B.Tech / B.E.", "MBA"], "B.Tech / B.E."),
    ("branch", "CSE", ["Computer Science and Engineering", "Electronics and Communication Engineering",
                       "Mechanical Engineering"], "Computer Science and Engineering"),
    ("branch", "CSE", ["CSE (AI & ML)", "CSE (Data Science)"], None),
    ("branch", "CSE", ["CSE", "CSE (AI & ML)"], "CSE"),
    ("branch", "IT", ["Information Technology", "CSE"], "Information Technology"),
    ("college", "VIT-AP University", ["VIT-AP University", "Vellore Institute of Technology"], "VIT-AP University"),
    ("college", "VIT", ["Vellore Institute of Technology", "VIT-AP University"], "Vellore Institute of Technology"),
    ("college", "Anna University", ["Vellore Institute of Technology", "IIT Madras"], None),
    ("state", "Andhra Pradesh", ["Andhra Pradesh", "Tamil Nadu"], "Andhra Pradesh"),
    ("state", "Andhra Pradesh", ["AP", "Telangana"], None),
    ("graduation_year", "2028", ["2026", "2027", "2028", "2029"], "2028"),
    ("graduation_year", "2028", ["2024-2028", "2023-2027"], "2024-2028"),
    ("college", "Foo University", ["Other", "Foo University"], "Foo University"),
    ("state", "Kerala", ["Other (specify)"], None),
    ("target_role", "AI Engineer", ["AI Engineer", "Web Developer"], "AI Engineer"),
    ("target_role", "ML Engineer", ["AI Engineer", "Web Developer"], None),
    ("branch", None, ["CSE"], None),
]


@pytest.mark.parametrize("field,value,options,expected", CASES)
def test_match_option(field, value, options, expected):
    assert match_option(field, value, options)["option"] == expected


def test_checkboxes():
    r = match_checkboxes(["Python", "Java", "SQL"], ["Python", "Machine Learning", "Photoshop", "SQL", "Tally"])
    assert r["options"] == ["Python", "SQL"]
    assert match_checkboxes(["C++"], ["C", "C++"])["options"] == ["C++"]
    assert match_checkboxes(["Python"], ["Tally", "Photoshop"])["options"] == []
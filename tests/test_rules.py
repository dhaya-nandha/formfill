import pytest

from src import rules


# ----- email -----
@pytest.mark.parametrize("text,expected", [
    ("Email: John.Doe@Gmail.com | 98765", "john.doe@gmail.com"),
    ("a@b.com and c@d.com", "a@b.com"),
    ("no email here", None),
    ("reach me: first.last+tag@sub.domain.co.in.", "first.last+tag@sub.domain.co.in"),
    (None, None),
])
def test_email(text, expected):
    assert rules.extract_email(text) == expected


# ----- phone -----
@pytest.mark.parametrize("text,expected", [
    ("+91 98765 43210", "9876543210"),
    ("98765-43210", "9876543210"),
    ("+91-9876543210", "9876543210"),
    ("(+91) 98765 43210", "9876543210"),
    ("9876543210", "9876543210"),
    ("919876543210", "9876543210"),
    ("Mobile: 098765 43210", "9876543210"),
    ("Ph: +91 98765 43210 / 91234 56789", "9876543210"),
    ("2023 - 2027 9876543210", "9876543210"),
    ("5876543210", None),
    ("12345", None),
    ("Aadhaar 123456789012", None),
    (None, None),
])
def test_phone(text, expected):
    assert rules.extract_phone(text) == expected


# ----- CGPA -----
@pytest.mark.parametrize("text,expected", [
    ("CGPA: 8.4/10", 8.4),
    ("CGPA - 8.24", 8.24),
    ("8.7 CGPA", 8.7),
    ("GPA 9.1", 9.1),
    ("Cumulative GPA: 8.0/10", 8.0),
    ("CGPA (out of 10): 8.4", 8.4),
    ("Achieved CGPA of 8.4 in semester 5", 8.4),
    ("Scored 8.5/10 overall", 8.5),
    ("Aggregate: 8.4", 8.4),
    ("Aggregate: 85%", None),
    ("Percentage: 85%", None),
    ("CGPA: 85%", None),
    ("GPA: 3.8/4.0", None),
    ("CGPA: 11.5", None),
    ("Date 08/10/2023", None),
    ("Class X CGPA: 9.8", None),
    ("B.Tech CGPA: 8.1 | Class XII: 92%", 8.1),
    ("Class XII: 92% | B.Tech CGPA: 8.4", 8.4),
    ("XYZ Public School (CBSE), 2021\nCGPA: 9.4\nVIT-AP University\nB.Tech CSE\nCGPA: 8.1", 8.1),
    ("7.4 Aggregate", 7.4),
    ("9.56 Cumulative GPA", 9.56),
    ("85 % Aggregate", None),
])
def test_cgpa(text, expected):
    assert rules.extract_cgpa(text) == expected


# ----- links -----
def test_github():
    assert rules.extract_github("github.com/dhaya-nandha") == "https://github.com/dhaya-nandha"
    assert rules.extract_github("https://github.com/dhaya-nandha/f1-wim") == "https://github.com/dhaya-nandha"
    assert rules.extract_github("GitHub: github.com/Foo-Bar | LinkedIn") == "https://github.com/Foo-Bar"
    assert rules.extract_github("https://gist.github.com/x") is None
    assert rules.extract_github("no link") is None


def test_linkedin():
    assert rules.extract_linkedin("linkedin.com/in/m-dhayanandha-1b68ab2a3/") == \
        "https://www.linkedin.com/in/m-dhayanandha-1b68ab2a3"
    assert rules.extract_linkedin("https://in.linkedin.com/in/john") == "https://www.linkedin.com/in/john"
    assert rules.extract_linkedin("linkedin.com/company/foo") is None
    assert rules.extract_linkedin("LinkedIn: john") is None


# ----- graduation year -----
@pytest.mark.parametrize("text,expected", [
    ("EDUCATION\nVIT-AP University, Amaravati\nB.Tech CSE   2024 - 2028\nCGPA: 8.2\n"
     "PROJECTS\nF1 App 2026 - 2027", "2028"),
    ("Education\nXYZ Public School 2019 - 2021\nABC College, B.Tech, Aug 2023 – May 2027", "2027"),
    ("B.Tech in Computer Science, Expected 2027", "2027"),
    ("B.Tech 2023-27", "2027"),
    ("Education\nABC University\nClass of 2027", "2027"),
    ("B.Tech CSE 2023 - Present", None),
    ("Education\nM.Tech 2027 - 2029\nB.Tech 2023 - 2027", "2029"),
    ("B.Tech 08/2023 - 05/2027", "2027"),
    ("• EDUCATION •\nXYZ University 2022 - 2026", "2026"),
    ("Skills: Python", None),
    ("Education\nVIT University, B.Tech Sept 2023 – Present\nSri Chaitanya Junior College June 2021 – March 2023 Intermediate", None),
    ("Education\nVIT, Jul 2024 — Present\nB.Tech CSE\nThe Amaatra Academy May 2022 — May 2024\nCBSE affiliated school - Percentage: 90.4%", None),
])
def test_graduation_year(text, expected):
    assert rules.extract_graduation_year(text) == expected


# ----- branch / degree -----
@pytest.mark.parametrize("text,expected", [
    ("CSE", "CSE"),
    ("Computer Science", "CSE"),
    ("Computer Science and Engineering (AI/ML)", "CSE"),
    ("CSE (AI & ML)", "AIML"),
    ("CSE (AIML)", "AIML"),
    ("IT", "IT"),
    ("Information Technology", "IT"),
    ("Electronics & Communication Engineering", "ECE"),
    ("Mechanical", "MECH"),
    ("Civil Engineering", "CIVIL"),
    ("Artificial Intelligence and Data Science", "AIDS"),
    ("AI&DS", "AIDS"),
    ("Basket Weaving", None),
    ("", None),
    ("I want to work in IT sector at a big company today", None),
])
def test_branch(text, expected):
    assert rules.normalize_branch(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("B.Tech", "B.Tech"),
    ("BTech", "B.Tech"),
    ("b tech", "B.Tech"),
    ("Bachelor of Technology", "B.Tech"),
    ("B.Tech Computer Science and Engineering (AI/ML)", "B.Tech"),
    ("B.E.", "B.E."),
    ("BE", "B.E."),
    ("BCA", "BCA"),
    ("Bachelor of Computer Applications", "BCA"),
    ("M.Tech", "M.Tech"),
    ("MCA", "MCA"),
    ("Bachelor of Science", "B.Sc"),
    ("MBA", "MBA"),
    ("random words", None),
])
def test_degree(text, expected):
    assert rules.normalize_degree(text) == expected


# ----- state / location -----
@pytest.mark.parametrize("text,expected", [
    ("Amaravati, Andhra Pradesh", "Andhra Pradesh"),
    ("Hyderabad, Telangana, India", "Telangana"),
    ("New Delhi", "Delhi"),
    ("Jammu & Kashmir", "Jammu and Kashmir"),
    ("Tamil Nadu 600001", "Tamil Nadu"),
    ("Bengaluru", None),
])
def test_state(text, expected):
    assert rules.lookup_state(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Amaravati, Andhra Pradesh", ("Amaravati", "Andhra Pradesh")),
    ("Vijayawada, Andhra Pradesh, India", ("Vijayawada", "Andhra Pradesh")),
    ("Hyderabad", ("Hyderabad", None)),
    ("Telangana", (None, "Telangana")),
    ("New Delhi, Delhi", ("New Delhi", "Delhi")),
    ("", (None, None)),
])
def test_split_location(text, expected):
    assert rules.split_location(text) == expected
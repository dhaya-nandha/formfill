import pytest

from src.pipeline import id_override


@pytest.mark.parametrize("q,field,expected", [
    ("X % or CGPA", "cgpa", "unsupported"),
    ("XII % or CGPA", "cgpa", "unsupported"),
    ("10th percentage", "cgpa", "unsupported"),
    ("Class 12 CGPA", "cgpa", "unsupported"),
    ("Secondary school CGPA", "cgpa", "unsupported"),
    ("12th passing year", "graduation_year", "unsupported"),
    ("School name", "college", "unsupported"),
    ("UG CGPA", "cgpa", "cgpa"),
    ("CGPA (out of 10)", "cgpa", "cgpa"),
    ("Current CGPA", "cgpa", "cgpa"),
    ("Graduation year", "graduation_year", "graduation_year"),
    ("College name", "college", "college"),
    ("PAN number", "phone", "unsupported"),
    ("Phone", "phone", "phone"),
    ("Year of study", "year_of_study", "year_of_study"),
])
def test_override(q, field, expected):
    assert id_override(q, field) == expected
import pytest

from app.db.story_name import parse_story_name


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("space_mage_1.docx", ("space_mage", 1)),
        ("Space_Mage_2.docx", ("space_mage", 2)),
        ("space_mage.docx", ("space_mage", 0)),
        ("Space Mage 10.pdf", ("space mage", 10)),
        ("space-mage-3.txt", ("space-mage", 3)),
        ("Explosive_Descent.docx", ("explosive_descent", 0)),
        ("2026.txt", ("2026", 0)),
    ],
)
def test_parse_story_name(filename, expected):
    assert parse_story_name(filename) == expected

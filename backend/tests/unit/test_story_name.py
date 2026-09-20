import pytest

from app.db.stories import assign_story
from app.db.story_name import parse_story_name


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("space_mage_1.docx", ("space_mage", 1)),
        ("Space_Mage_2.docx", ("space_mage", 2)),
        ("space_mage.docx", ("space_mage", 0)),
        ("Space Mage 10.pdf", ("space_mage", 10)),
        ("space-mage-3.txt", ("space_mage", 3)),
        ("Space - Mage 4.docx", ("space_mage", 4)),
        ("Explosive_Descent.docx", ("explosive_descent", 0)),
        ("Conspiratorial_ Device.docx", ("conspiratorial_device", 0)),
        ("  Conspiratorial__Device  2.docx", ("conspiratorial_device", 2)),
        ("2026.txt", ("2026", 0)),
    ],
)
def test_parse_story_name(filename, expected):
    assert parse_story_name(filename) == expected


def test_differently_separated_names_group_into_one_story(db_conn):
    story_ids = set()
    for filename in ("Space Mage.docx", "space_mage_2.docx", "Space-Mage-3.docx"):
        document_id = db_conn.execute(
            "INSERT INTO documents (role, source_path, filename, source_type, content_hash, ingested_at) "
            "VALUES ('draft_script', ?, ?, 'docx', ?, 'now')",
            (f"/x/{filename}", filename, filename),
        ).lastrowid
        assign_story(db_conn, document_id)
        story_ids.add(db_conn.execute("SELECT story_id FROM documents WHERE id = ?", (document_id,)).fetchone()[0])

    assert len(story_ids) == 1
    assert [row[0] for row in db_conn.execute("SELECT filename FROM documents ORDER BY story_position")] == [
        "Space Mage.docx",
        "space_mage_2.docx",
        "Space-Mage-3.docx",
    ]

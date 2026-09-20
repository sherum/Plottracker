from app.db import repository
from app.db.connection import _migrate_stories
from app.db.stories import assign_story, get_or_create_story


def _add_document(db_conn, filename, role="draft_script"):
    document_id = db_conn.execute(
        "INSERT INTO documents (role, source_path, filename, source_type, content_hash, ingested_at) "
        "VALUES (?, ?, ?, 'docx', ?, 'now')",
        (role, f"/x/{filename}", filename, filename),
    ).lastrowid
    return document_id


def _story_names(db_conn, story_id):
    return [
        (row["name"], row["rank"])
        for row in db_conn.execute("SELECT name, rank FROM story_names WHERE story_id = ? ORDER BY rank, name", (story_id,))
    ]


def test_a_new_story_owns_its_own_name_at_rank_zero(db_conn):
    story_id = get_or_create_story(db_conn, "saga")

    assert _story_names(db_conn, story_id) == [("saga", 0)]


def test_a_name_owned_by_another_story_resolves_to_that_story(db_conn):
    story_a = get_or_create_story(db_conn, "book_one")
    db_conn.execute("INSERT INTO story_names (name, story_id, rank) VALUES ('book_two', ?, 1)", (story_a,))

    assert get_or_create_story(db_conn, "book_two") == story_a
    assert db_conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 1


def test_a_story_is_ordered_by_name_rank_then_number_then_upload(db_conn):
    story_a = get_or_create_story(db_conn, "book_one")
    db_conn.execute("INSERT INTO story_names (name, story_id, rank) VALUES ('book_two', ?, 1)", (story_a,))
    documents = [_add_document(db_conn, name) for name in ("book_two_2.docx", "book_two.docx", "book_one_2.docx", "book_one.docx")]
    for document_id in documents:
        assign_story(db_conn, document_id)

    ordered = [row["filename"] for row in db_conn.execute("SELECT filename FROM documents ORDER BY story_position")]

    assert ordered == ["book_one.docx", "book_one_2.docx", "book_two.docx", "book_two_2.docx"]


def test_existing_stories_are_given_their_names_by_the_migration(db_conn):
    db_conn.execute("INSERT INTO stories (name, created_at) VALUES ('legacy', 'now')")

    _migrate_stories(db_conn)
    _migrate_stories(db_conn)

    story_id = db_conn.execute("SELECT id FROM stories WHERE name = 'legacy'").fetchone()[0]
    assert _story_names(db_conn, story_id) == [("legacy", 0)]

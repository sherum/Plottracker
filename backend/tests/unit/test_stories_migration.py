import sqlite3

import pytest

from app.db.connection import _migrate_stories


def _add_document(conn, filename, story_position=None):
    cursor = conn.execute(
        "INSERT INTO documents (role, source_path, filename, source_type, content_hash, ingested_at, story_position) "
        "VALUES ('draft_script', ?, ?, 'docx', ?, 'now', ?)",
        (f"/x/{filename}", filename, filename, story_position),
    )
    return cursor.lastrowid


def _story_of(conn, document_id):
    return conn.execute(
        "SELECT stories.name FROM documents JOIN stories ON stories.id = documents.story_id WHERE documents.id = ?",
        (document_id,),
    ).fetchone()["name"]


def test_documents_with_same_base_name_share_a_story(db_conn):
    first = _add_document(db_conn, "space_mage_1.docx")
    second = _add_document(db_conn, "Space_Mage_2.docx")
    unnumbered = _add_document(db_conn, "space_mage.docx")
    other = _add_document(db_conn, "explosive_descent.docx")

    _migrate_stories(db_conn)

    assert _story_of(db_conn, first) == _story_of(db_conn, second) == _story_of(db_conn, unnumbered) == "space_mage"
    assert _story_of(db_conn, other) == "explosive_descent"
    assert db_conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 2


def test_migration_is_idempotent(db_conn):
    _add_document(db_conn, "space_mage_1.docx")

    _migrate_stories(db_conn)
    _migrate_stories(db_conn)

    assert db_conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 1


def _insert_main(conn, story_id):
    conn.execute(
        "INSERT INTO themes (title, summary, is_main, story_id, created_at) VALUES ('Main', '', 1, ?, 'now')",
        (story_id,),
    )


def test_existing_main_theme_goes_to_the_story_in_use(db_conn):
    # a fresh database already holds one Main theme that belongs to no story yet
    _add_document(db_conn, "other_1.docx")
    in_use = _add_document(db_conn, "space_mage_1.docx", story_position=1)

    _migrate_stories(db_conn)

    main_story = db_conn.execute(
        "SELECT stories.name FROM themes JOIN stories ON stories.id = themes.story_id WHERE is_main = 1"
    ).fetchone()["name"]
    assert main_story == _story_of(db_conn, in_use)


def test_stories_can_share_a_position_number_and_each_have_a_main(db_conn):
    _add_document(db_conn, "a_1.docx", story_position=1)
    _add_document(db_conn, "b_1.docx", story_position=1)

    _migrate_stories(db_conn)

    story_without_main = db_conn.execute(
        "SELECT id FROM stories WHERE id NOT IN (SELECT story_id FROM themes WHERE is_main = 1)"
    ).fetchone()[0]
    _insert_main(db_conn, story_without_main)
    assert db_conn.execute("SELECT COUNT(*) FROM themes WHERE is_main = 1").fetchone()[0] == 2


def test_a_story_cannot_have_two_main_themes_or_repeat_a_position(db_conn):
    _add_document(db_conn, "a_1.docx", story_position=1)
    duplicate = _add_document(db_conn, "a_2.docx")
    _migrate_stories(db_conn)
    story_id = db_conn.execute("SELECT id FROM stories").fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute("UPDATE documents SET story_position = 1 WHERE id = ?", (duplicate,))
    with pytest.raises(sqlite3.IntegrityError):
        _insert_main(db_conn, story_id)

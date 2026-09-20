import sqlite3
from datetime import datetime, timezone

from app.db.story_name import parse_story_name


def get_or_create_story(conn: sqlite3.Connection, name: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO stories (name, created_at) VALUES (?, ?)",
        (name, datetime.now(timezone.utc).isoformat()),
    )
    return conn.execute("SELECT id FROM stories WHERE name = ?", (name,)).fetchone()["id"]


def assign_story(conn: sqlite3.Connection, document_id: int) -> None:
    """Place a document in the story its filename names, and reorder that story.

    A rename can move a document between stories, so the story it left is
    reordered too.
    """
    document = conn.execute("SELECT filename, story_id FROM documents WHERE id = ?", (document_id,)).fetchone()
    name, _ = parse_story_name(document["filename"])
    story_id = get_or_create_story(conn, name)
    conn.execute("UPDATE documents SET story_id = ? WHERE id = ?", (story_id, document_id))

    for affected in {story_id, document["story_id"]} - {None}:
        order_story(conn, affected)
    conn.commit()


def order_story(conn: sqlite3.Connection, story_id: int) -> None:
    """Number a story's manuscripts by their filename number, then by upload order."""
    rows = conn.execute(
        "SELECT id, filename FROM documents WHERE story_id = ? AND role = 'draft_script'", (story_id,)
    ).fetchall()
    ordered = sorted(rows, key=lambda row: (parse_story_name(row["filename"])[1], row["id"]))

    # Clear first so the unique (story, position) index never sees a clash mid-update.
    conn.execute("UPDATE documents SET story_position = NULL WHERE story_id = ?", (story_id,))
    for position, row in enumerate(ordered, start=1):
        conn.execute("UPDATE documents SET story_position = ? WHERE id = ?", (position, row["id"]))

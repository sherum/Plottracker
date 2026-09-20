import sqlite3

from app.db.stories import ensure_main_theme, get_or_create_story, order_story
from app.db.story_name import parse_story_name

_LAST_POSITION_SQL = """
    (
        SELECT MAX(documents.story_position) FROM topics
        JOIN documents ON documents.id = topics.document_id
        WHERE topics.theme_id = subplots.theme_id AND topics.excluded = 0
    )
"""


def _main_theme_id(conn: sqlite3.Connection, story_id: int) -> int:
    ensure_main_theme(conn, story_id)
    return conn.execute("SELECT id FROM themes WHERE is_main = 1 AND story_id = ?", (story_id,)).fetchone()["id"]


def link_stories(conn: sqlite3.Connection, first_id: int, second_id: int) -> int:
    """Merge the second story into the first: one Main theme, first's documents then second's.

    Returns the surviving story id (the first).
    """
    if first_id == second_id:
        raise ValueError("a story cannot be linked to itself")

    first_main, second_main = _main_theme_id(conn, first_id), _main_theme_id(conn, second_id)
    documents_before = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE story_id = ? AND story_position IS NOT NULL", (first_id,)
    ).fetchone()[0]
    next_rank = conn.execute("SELECT MAX(rank) + 1 FROM story_names WHERE story_id = ?", (first_id,)).fetchone()[0]

    # A subplot's recorded resolution point is a position in its own story's order;
    # in the merged story the second story's editions all come after the first's.
    conn.execute(
        """
        UPDATE subplots SET resolved_at_position = resolved_at_position + ?
        WHERE resolved_at_position IS NOT NULL
          AND theme_id IN (SELECT id FROM themes WHERE story_id = ?)
        """,
        (documents_before, second_id),
    )

    conn.execute("UPDATE story_names SET story_id = ?, rank = rank + ? WHERE story_id = ?", (first_id, next_rank, second_id))
    conn.execute("UPDATE documents SET story_position = NULL WHERE story_id = ?", (second_id,))
    conn.execute("UPDATE documents SET story_id = ? WHERE story_id = ?", (first_id, second_id))

    conn.execute("UPDATE topics SET theme_id = ? WHERE theme_id = ?", (first_main, second_main))
    conn.execute("DELETE FROM themes WHERE id = ?", (second_main,))
    conn.execute("UPDATE themes SET story_id = ? WHERE story_id = ?", (first_id, second_id))
    conn.execute("DELETE FROM stories WHERE id = ?", (second_id,))

    order_story(conn, first_id)
    conn.commit()
    return first_id


def unlink_story(conn: sqlite3.Connection, story_id: int) -> int:
    """Detach the last-linked name from a story into a story of its own; returns that new story's id.

    Repeated calls undo a chain of links from the end. Main topics follow their
    document. A subplot stays with the earlier story if it has topics there, and
    its topics in the detached documents move to the new story's Main.
    """
    names = conn.execute("SELECT name FROM story_names WHERE story_id = ? ORDER BY rank, name", (story_id,)).fetchall()
    if len(names) < 2:
        raise ValueError("this story is not linked to another")
    detached_name = names[-1]["name"]

    documents = conn.execute("SELECT id, filename FROM documents WHERE story_id = ?", (story_id,)).fetchall()
    detached_ids = [d["id"] for d in documents if parse_story_name(d["filename"])[0] == detached_name]

    conn.execute("DELETE FROM story_names WHERE name = ?", (detached_name,))
    new_id = get_or_create_story(conn, detached_name)
    new_main = _main_theme_id(conn, new_id)

    marks = ",".join("?" * len(detached_ids))
    conn.execute(f"UPDATE documents SET story_position = NULL WHERE id IN ({marks})", detached_ids)
    conn.execute(f"UPDATE documents SET story_id = ? WHERE id IN ({marks})", [new_id, *detached_ids])

    # A subplot living only in the detached documents goes with them.
    for theme in conn.execute("SELECT id FROM themes WHERE story_id = ? AND is_main = 0", (story_id,)).fetchall():
        homes = {
            row["story_id"]
            for row in conn.execute(
                "SELECT DISTINCT documents.story_id FROM topics JOIN documents ON documents.id = topics.document_id "
                "WHERE topics.theme_id = ?",
                (theme["id"],),
            )
        }
        if homes == {new_id}:
            conn.execute("UPDATE themes SET story_id = ? WHERE id = ?", (new_id, theme["id"]))

    # Any topic whose theme now belongs to another story falls back to its own story's Main.
    conn.execute(
        f"""
        UPDATE topics SET theme_id = ?
        WHERE document_id IN ({marks})
          AND theme_id NOT IN (SELECT id FROM themes WHERE story_id = ?)
        """,
        [new_main, *detached_ids, new_id],
    )

    for affected in (story_id, new_id):
        order_story(conn, affected)
        conn.execute(
            f"""
            UPDATE subplots SET resolved_at_position = {_LAST_POSITION_SQL}
            WHERE resolved = 1 AND theme_id IN (SELECT id FROM themes WHERE story_id = ?)
            """,
            (affected,),
        )
    conn.commit()
    return new_id

import sqlite3
from datetime import datetime, timezone


def insert_document(
    conn: sqlite3.Connection,
    *,
    role: str,
    source_path: str,
    filename: str,
    source_type: str,
    content_hash: str,
    page_count: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO documents (role, source_path, filename, source_type, content_hash, ingested_at, page_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            role,
            source_path,
            filename,
            source_type,
            content_hash,
            datetime.now(timezone.utc).isoformat(),
            page_count,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_segment(
    conn: sqlite3.Connection,
    *,
    document_id: int,
    sequence_index: int,
    text: str,
    page_number: int | None = None,
    paragraph_index: int | None = None,
    char_start: int | None = None,
    char_end: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO segments (document_id, sequence_index, page_number, paragraph_index, text, char_start, char_end)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (document_id, sequence_index, page_number, paragraph_index, text, char_start, char_end),
    )
    conn.commit()
    return cursor.lastrowid


def insert_style(
    conn: sqlite3.Connection,
    *,
    segment_id: int,
    style_kind: str,
    style_value: str | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO segment_styles (segment_id, style_kind, style_value) VALUES (?, ?, ?)",
        (segment_id, style_kind, style_value),
    )
    conn.commit()
    return cursor.lastrowid


def list_documents(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM documents ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def insert_topic(
    conn: sqlite3.Connection,
    *,
    document_id: int,
    sequence_index: int,
    title: str,
    summary: str,
    segment_start_id: int,
    segment_end_id: int,
    act: str | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO topics (document_id, sequence_index, title, summary, segment_start_id, segment_end_id, act, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_id,
            sequence_index,
            title,
            summary,
            segment_start_id,
            segment_end_id,
            act,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def insert_theme(conn: sqlite3.Connection, *, title: str, summary: str) -> int:
    cursor = conn.execute(
        "INSERT INTO themes (title, summary, created_at) VALUES (?, ?, ?)",
        (title, summary, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def set_topic_theme(conn: sqlite3.Connection, topic_id: int, theme_id: int) -> None:
    conn.execute("UPDATE topics SET theme_id = ? WHERE id = ?", (theme_id, topic_id))
    conn.commit()


def list_topics(conn: sqlite3.Connection, document_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM topics WHERE document_id = ? ORDER BY sequence_index",
        (document_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_themes(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM themes ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def list_all_topics(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT topics.*, documents.filename AS document_filename
        FROM topics
        JOIN documents ON documents.id = topics.document_id
        ORDER BY topics.document_id, topics.sequence_index
        """
    ).fetchall()
    return [dict(row) for row in rows]


def update_topic(conn: sqlite3.Connection, topic_id: int, *, title: str, summary: str) -> dict:
    conn.execute("UPDATE topics SET title = ?, summary = ? WHERE id = ?", (title, summary, topic_id))
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return dict(row)


def update_theme(conn: sqlite3.Connection, theme_id: int, *, title: str, summary: str) -> dict:
    conn.execute("UPDATE themes SET title = ?, summary = ? WHERE id = ?", (title, summary, theme_id))
    conn.commit()
    row = conn.execute("SELECT * FROM themes WHERE id = ?", (theme_id,)).fetchone()
    return dict(row)


def insert_subplot(conn: sqlite3.Connection, *, title: str, summary: str, theme_id: int | None = None) -> int:
    cursor = conn.execute(
        "INSERT INTO subplots (theme_id, title, summary, created_at) VALUES (?, ?, ?, ?)",
        (theme_id, title, summary, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def get_subplot(conn: sqlite3.Connection, subplot_id: int) -> dict:
    row = conn.execute(
        """
        SELECT subplots.*, themes.title AS theme_title,
               (SELECT COUNT(*) FROM subplot_topics WHERE subplot_topics.subplot_id = subplots.id) AS topic_count
        FROM subplots
        LEFT JOIN themes ON themes.id = subplots.theme_id
        WHERE subplots.id = ?
        """,
        (subplot_id,),
    ).fetchone()
    return dict(row)


def list_subplots(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT subplots.*, themes.title AS theme_title,
               (SELECT COUNT(*) FROM subplot_topics WHERE subplot_topics.subplot_id = subplots.id) AS topic_count
        FROM subplots
        LEFT JOIN themes ON themes.id = subplots.theme_id
        ORDER BY subplots.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def add_topic_to_subplot(conn: sqlite3.Connection, subplot_id: int, topic_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO subplot_topics (subplot_id, topic_id) VALUES (?, ?)",
        (subplot_id, topic_id),
    )
    conn.commit()


def remove_topic_from_subplot(conn: sqlite3.Connection, subplot_id: int, topic_id: int) -> None:
    conn.execute(
        "DELETE FROM subplot_topics WHERE subplot_id = ? AND topic_id = ?",
        (subplot_id, topic_id),
    )
    conn.commit()


def list_subplot_topics(conn: sqlite3.Connection, subplot_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT topics.*, documents.filename AS document_filename
        FROM subplot_topics
        JOIN topics ON topics.id = subplot_topics.topic_id
        JOIN documents ON documents.id = topics.document_id
        WHERE subplot_topics.subplot_id = ?
        ORDER BY topics.document_id, topics.sequence_index
        """,
        (subplot_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def promote_theme_to_subplot(conn: sqlite3.Connection, theme_id: int) -> int:
    theme = conn.execute("SELECT * FROM themes WHERE id = ?", (theme_id,)).fetchone()
    subplot_id = insert_subplot(conn, title=theme["title"], summary=theme["summary"], theme_id=theme_id)
    topic_rows = conn.execute("SELECT id FROM topics WHERE theme_id = ?", (theme_id,)).fetchall()
    for row in topic_rows:
        add_topic_to_subplot(conn, subplot_id, row["id"])
    return subplot_id


def get_segments(conn: sqlite3.Connection, document_id: int) -> list[dict]:
    segment_rows = conn.execute(
        "SELECT * FROM segments WHERE document_id = ? ORDER BY sequence_index",
        (document_id,),
    ).fetchall()

    segments = []
    for row in segment_rows:
        segment = dict(row)
        style_rows = conn.execute(
            "SELECT style_kind, style_value FROM segment_styles WHERE segment_id = ?",
            (segment["id"],),
        ).fetchall()
        segment["styles"] = [dict(style_row) for style_row in style_rows]
        segments.append(segment)

    return segments

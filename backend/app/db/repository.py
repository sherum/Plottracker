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


def delete_document(conn: sqlite3.Connection, document_id: int) -> None:
    conn.execute(
        "DELETE FROM subplot_topics WHERE topic_id IN (SELECT id FROM topics WHERE document_id = ?)",
        (document_id,),
    )
    conn.execute("DELETE FROM topics WHERE document_id = ?", (document_id,))
    conn.execute(
        "DELETE FROM segment_styles WHERE segment_id IN (SELECT id FROM segments WHERE document_id = ?)",
        (document_id,),
    )
    conn.execute("DELETE FROM segments WHERE document_id = ?", (document_id,))
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()


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
        SELECT topics.*, documents.filename AS document_filename,
            (SELECT page_number FROM segments WHERE id = topics.segment_start_id) AS page_number,
            (
                SELECT segments.text
                FROM segments
                JOIN segment_styles ON segment_styles.segment_id = segments.id
                WHERE segments.document_id = topics.document_id
                    AND segment_styles.style_kind = 'heading'
                    AND segments.sequence_index <= (
                        SELECT sequence_index FROM segments WHERE id = topics.segment_start_id
                    )
                ORDER BY segments.sequence_index DESC
                LIMIT 1
            ) AS chapter_title
        FROM topics
        JOIN documents ON documents.id = topics.document_id
        ORDER BY topics.document_id, topics.sequence_index
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_topics_by_ids(conn: sqlite3.Connection, topic_ids: list[int]) -> list[dict]:
    if not topic_ids:
        return []
    placeholders = ",".join("?" * len(topic_ids))
    rows = conn.execute(
        f"SELECT * FROM topics WHERE id IN ({placeholders}) AND excluded = 0", topic_ids
    ).fetchall()
    return [dict(row) for row in rows]


def get_themes_by_ids(conn: sqlite3.Connection, theme_ids: list[int]) -> list[dict]:
    if not theme_ids:
        return []
    placeholders = ",".join("?" * len(theme_ids))
    rows = conn.execute(
        f"SELECT * FROM themes WHERE id IN ({placeholders}) AND excluded = 0", theme_ids
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


def set_topic_excluded(conn: sqlite3.Connection, topic_id: int, excluded: bool) -> dict:
    conn.execute("UPDATE topics SET excluded = ? WHERE id = ?", (int(excluded), topic_id))
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return dict(row)


def set_topic_act(conn: sqlite3.Connection, topic_id: int, act: str | None) -> dict:
    conn.execute("UPDATE topics SET act = ? WHERE id = ?", (act, topic_id))
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return dict(row)


def unassign_topic_theme(conn: sqlite3.Connection, topic_id: int) -> dict:
    conn.execute("UPDATE topics SET theme_id = NULL WHERE id = ?", (topic_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    return dict(row)


def set_theme_excluded(conn: sqlite3.Connection, theme_id: int, excluded: bool) -> dict:
    conn.execute("UPDATE themes SET excluded = ? WHERE id = ?", (int(excluded), theme_id))
    conn.commit()
    row = conn.execute("SELECT * FROM themes WHERE id = ?", (theme_id,)).fetchone()
    return dict(row)


def exclude_topics_for_document(conn: sqlite3.Connection, document_id: int) -> None:
    conn.execute("UPDATE topics SET excluded = 1 WHERE document_id = ?", (document_id,))
    conn.commit()


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
               (
                   SELECT COUNT(*) FROM subplot_topics
                   JOIN topics ON topics.id = subplot_topics.topic_id
                   WHERE subplot_topics.subplot_id = subplots.id AND topics.excluded = 0
               ) AS topic_count
        FROM subplots
        LEFT JOIN themes ON themes.id = subplots.theme_id
        WHERE subplots.id = ?
        """,
        (subplot_id,),
    ).fetchone()
    return dict(row)


def list_subplots(conn: sqlite3.Connection, document_id: int | None = None) -> list[dict]:
    rows = conn.execute(
        """
        SELECT subplots.*, themes.title AS theme_title,
               (
                   SELECT COUNT(*) FROM subplot_topics
                   JOIN topics ON topics.id = subplot_topics.topic_id
                   WHERE subplot_topics.subplot_id = subplots.id AND topics.excluded = 0
               ) AS topic_count
        FROM subplots
        LEFT JOIN themes ON themes.id = subplots.theme_id
        WHERE (
            ? IS NULL
            OR EXISTS (
                SELECT 1 FROM subplot_topics
                JOIN topics ON topics.id = subplot_topics.topic_id
                WHERE subplot_topics.subplot_id = subplots.id AND topics.document_id = ?
            )
            OR EXISTS (
                SELECT 1 FROM topics
                WHERE topics.theme_id = subplots.theme_id AND topics.document_id = ?
            )
        )
        ORDER BY subplots.id
        """,
        (document_id, document_id, document_id),
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


def delete_subplot(conn: sqlite3.Connection, subplot_id: int) -> None:
    conn.execute("DELETE FROM subplot_topics WHERE subplot_id = ?", (subplot_id,))
    conn.execute("DELETE FROM subplots WHERE id = ?", (subplot_id,))
    conn.commit()


def list_subplot_topic_ids(conn: sqlite3.Connection, subplot_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT topic_id FROM subplot_topics WHERE subplot_id = ?", (subplot_id,)
    ).fetchall()
    return [row["topic_id"] for row in rows]


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


def create_named_subplot_from_theme(conn: sqlite3.Connection, theme_id: int, title: str) -> int:
    theme = conn.execute("SELECT * FROM themes WHERE id = ?", (theme_id,)).fetchone()
    summary = theme["summary"] if theme else ""
    return insert_subplot(conn, title=title, summary=summary, theme_id=theme_id)


def insert_encoding_rule(
    conn: sqlite3.Connection,
    *,
    style_kind: str,
    block_length: str,
    position: str,
    label: str,
    description: str = "",
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO encoding_rules (style_kind, block_length, position, label, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (style_kind, block_length, position, label, description, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def list_encoding_rules(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM encoding_rules ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def update_encoding_rule(
    conn: sqlite3.Connection,
    rule_id: int,
    *,
    style_kind: str,
    block_length: str,
    position: str,
    label: str,
    description: str,
) -> dict:
    conn.execute(
        """
        UPDATE encoding_rules
        SET style_kind = ?, block_length = ?, position = ?, label = ?, description = ?
        WHERE id = ?
        """,
        (style_kind, block_length, position, label, description, rule_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM encoding_rules WHERE id = ?", (rule_id,)).fetchone()
    return dict(row)


def delete_encoding_rule(conn: sqlite3.Connection, rule_id: int) -> None:
    conn.execute("DELETE FROM encoding_rules WHERE id = ?", (rule_id,))
    conn.commit()


def clear_semantic_styles_for_document(conn: sqlite3.Connection, document_id: int) -> None:
    conn.execute(
        """
        DELETE FROM segment_styles
        WHERE style_kind = 'semantic'
        AND segment_id IN (SELECT id FROM segments WHERE document_id = ?)
        """,
        (document_id,),
    )
    conn.commit()


def get_topic_source_text(conn: sqlite3.Connection, topic_id: int) -> str:
    rows = conn.execute(
        """
        SELECT s.text
        FROM segments s
        JOIN topics t ON t.document_id = s.document_id
        WHERE t.id = ?
          AND s.sequence_index BETWEEN
              (SELECT sequence_index FROM segments WHERE id = t.segment_start_id)
              AND (SELECT sequence_index FROM segments WHERE id = t.segment_end_id)
        ORDER BY s.sequence_index
        """,
        (topic_id,),
    ).fetchall()
    return "\n\n".join(row["text"] for row in rows)


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

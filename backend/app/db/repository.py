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


def get_document(conn: sqlite3.Connection, document_id: int) -> dict:
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return dict(row)


def update_document_path(conn: sqlite3.Connection, document_id: int, *, filename: str, source_path: str) -> dict:
    conn.execute(
        "UPDATE documents SET filename = ?, source_path = ? WHERE id = ?", (filename, source_path, document_id)
    )
    conn.commit()
    return get_document(conn, document_id)


def set_story_order(conn: sqlite3.Connection, document_ids: list[int]) -> None:
    # Clear first so the partial unique index never sees two documents claim
    # the same position while positions are being reassigned.
    conn.execute("UPDATE documents SET story_position = NULL")
    for position, document_id in enumerate(document_ids, start=1):
        conn.execute("UPDATE documents SET story_position = ? WHERE id = ?", (position, document_id))
    conn.commit()


def list_story_documents(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM documents WHERE story_position IS NOT NULL ORDER BY story_position"
    ).fetchall()
    return [dict(row) for row in rows]


def delete_document(conn: sqlite3.Connection, document_id: int) -> None:
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
    theme_id: int,
    sequence_index: int,
    title: str,
    summary: str,
    segment_start_id: int,
    segment_end_id: int,
    act: str | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO topics
            (document_id, theme_id, sequence_index, title, summary, segment_start_id, segment_end_id, act, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_id,
            theme_id,
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


def get_main_theme_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM themes WHERE is_main = 1").fetchone()
    return row["id"]


def retire_theme(conn: sqlite3.Connection, theme_id: int) -> None:
    main_theme_id = get_main_theme_id(conn)
    if theme_id == main_theme_id:
        return
    conn.execute("UPDATE topics SET theme_id = ? WHERE theme_id = ?", (main_theme_id, theme_id))
    conn.execute("DELETE FROM subplots WHERE theme_id = ?", (theme_id,))
    conn.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
    conn.commit()


def set_main_theme(conn: sqlite3.Connection, theme_id: int) -> None:
    old_main_id = get_main_theme_id(conn)
    if theme_id == old_main_id:
        return

    # Clear the old flag before setting the new one - the partial unique
    # index on is_main=1 would otherwise briefly see two rows with it set.
    conn.execute("UPDATE themes SET is_main = 0 WHERE id = ?", (old_main_id,))
    conn.execute("UPDATE themes SET is_main = 1 WHERE id = ?", (theme_id,))

    # Main never has a subplot - its topics (theme_id unchanged) now belong
    # to Main automatically. The old Main, now an ordinary theme, needs one.
    conn.execute("DELETE FROM subplots WHERE theme_id = ?", (theme_id,))
    insert_subplot(conn, theme_id=old_main_id)
    conn.commit()


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


def list_active_themes(conn: sqlite3.Connection) -> list[dict]:
    """Non-main, non-excluded themes - candidates to offer the LLM for reuse."""
    rows = conn.execute(
        "SELECT id, title, summary FROM themes WHERE is_main = 0 AND excluded = 0 ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]


def get_theme(conn: sqlite3.Connection, theme_id: int) -> dict:
    row = conn.execute("SELECT * FROM themes WHERE id = ?", (theme_id,)).fetchone()
    return dict(row)


def list_all_topics(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT topics.*, documents.filename AS document_filename, documents.story_position AS document_story_position,
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
        ORDER BY (documents.story_position IS NULL), documents.story_position, documents.id, topics.sequence_index
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


def move_topic(conn: sqlite3.Connection, topic_id: int, *, theme_id: int, act: str | None) -> dict:
    conn.execute("UPDATE topics SET theme_id = ?, act = ? WHERE id = ?", (theme_id, act, topic_id))
    conn.commit()
    row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
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
    main_theme_id = get_main_theme_id(conn)
    conn.execute("UPDATE topics SET theme_id = ? WHERE id = ?", (main_theme_id, topic_id))
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


def insert_subplot(
    conn: sqlite3.Connection, *, title: str | None = None, summary: str | None = None, theme_id: int | None = None
) -> int:
    # Every subplot has its own theme: reuse the one given, or create one from
    # the given title/summary so it's never left without one. A subplot has no
    # title/summary of its own - it always reads its theme's.
    if theme_id is None:
        theme_id = insert_theme(conn, title=title, summary=summary)
    cursor = conn.execute(
        "INSERT INTO subplots (theme_id, created_at) VALUES (?, ?)",
        (theme_id, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def get_subplot(conn: sqlite3.Connection, subplot_id: int) -> dict:
    row = conn.execute(
        """
        SELECT subplots.id, subplots.theme_id, subplots.created_at,
               themes.title AS title, themes.summary AS summary,
               (
                   SELECT COUNT(*) FROM topics
                   WHERE topics.theme_id = subplots.theme_id AND topics.excluded = 0
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
        SELECT subplots.id, subplots.theme_id, subplots.created_at,
               themes.title AS title, themes.summary AS summary,
               (
                   SELECT COUNT(*) FROM topics
                   WHERE topics.theme_id = subplots.theme_id AND topics.excluded = 0
               ) AS topic_count
        FROM subplots
        LEFT JOIN themes ON themes.id = subplots.theme_id
        WHERE (
            ? IS NULL
            OR EXISTS (
                SELECT 1 FROM topics
                WHERE topics.theme_id = subplots.theme_id AND topics.document_id = ?
            )
        )
        ORDER BY subplots.id
        """,
        (document_id, document_id),
    ).fetchall()
    return [dict(row) for row in rows]


def add_topic_to_subplot(conn: sqlite3.Connection, subplot_id: int, topic_id: int) -> None:
    conn.execute(
        "UPDATE topics SET theme_id = (SELECT theme_id FROM subplots WHERE id = ?) WHERE id = ?",
        (subplot_id, topic_id),
    )
    conn.commit()


def remove_topic_from_subplot(conn: sqlite3.Connection, subplot_id: int, topic_id: int) -> None:
    main_theme_id = get_main_theme_id(conn)
    conn.execute(
        """
        UPDATE topics SET theme_id = ?
        WHERE id = ? AND theme_id = (SELECT theme_id FROM subplots WHERE id = ?)
        """,
        (main_theme_id, topic_id, subplot_id),
    )
    conn.commit()


def delete_subplot(conn: sqlite3.Connection, subplot_id: int) -> None:
    row = conn.execute("SELECT theme_id FROM subplots WHERE id = ?", (subplot_id,)).fetchone()
    if row is not None:
        retire_theme(conn, row["theme_id"])


def list_subplot_topic_ids(conn: sqlite3.Connection, subplot_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT id FROM topics WHERE theme_id = (SELECT theme_id FROM subplots WHERE id = ?)",
        (subplot_id,),
    ).fetchall()
    return [row["id"] for row in rows]


def list_subplot_topics(conn: sqlite3.Connection, subplot_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT topics.*, documents.filename AS document_filename, documents.story_position AS document_story_position
        FROM topics
        JOIN documents ON documents.id = topics.document_id
        WHERE topics.theme_id = (SELECT theme_id FROM subplots WHERE id = ?)
        ORDER BY (documents.story_position IS NULL), documents.story_position, documents.id, topics.sequence_index
        """,
        (subplot_id,),
    ).fetchall()
    return [dict(row) for row in rows]


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


def get_topic_segments(conn: sqlite3.Connection, topic_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT s.id, s.text, s.sequence_index
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
    return [dict(row) for row in rows]


def split_topic(conn: sqlite3.Connection, topic_id: int, split_segment_id: int) -> dict:
    topic = dict(conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone())
    split_segment = conn.execute(
        "SELECT sequence_index FROM segments WHERE id = ?", (split_segment_id,)
    ).fetchone()

    prev_segment = conn.execute(
        "SELECT id FROM segments WHERE document_id = ? AND sequence_index < ? ORDER BY sequence_index DESC LIMIT 1",
        (topic["document_id"], split_segment["sequence_index"]),
    ).fetchone()

    conn.execute(
        "UPDATE topics SET sequence_index = sequence_index + 1 WHERE document_id = ? AND sequence_index > ?",
        (topic["document_id"], topic["sequence_index"]),
    )

    new_topic_id = insert_topic(
        conn,
        document_id=topic["document_id"],
        theme_id=topic["theme_id"],
        sequence_index=topic["sequence_index"] + 1,
        title=topic["title"],
        summary=topic["summary"],
        segment_start_id=split_segment_id,
        segment_end_id=topic["segment_end_id"],
        act=topic["act"],
    )

    conn.execute("UPDATE topics SET segment_end_id = ? WHERE id = ?", (prev_segment["id"], topic_id))
    conn.commit()

    return {
        "original": dict(conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()),
        "new": dict(conn.execute("SELECT * FROM topics WHERE id = ?", (new_topic_id,)).fetchone()),
    }


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

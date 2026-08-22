import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.config import settings

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text())
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    document_columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
    if "story_position" not in document_columns:
        conn.execute("ALTER TABLE documents ADD COLUMN story_position INTEGER")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_story_position "
        "ON documents(story_position) WHERE story_position IS NOT NULL"
    )

    topic_columns = {row[1] for row in conn.execute("PRAGMA table_info(topics)")}
    if "act" not in topic_columns:
        conn.execute("ALTER TABLE topics ADD COLUMN act TEXT CHECK (act IN ('opening', 'conflict', 'climax'))")
    if "excluded" not in topic_columns:
        conn.execute("ALTER TABLE topics ADD COLUMN excluded INTEGER NOT NULL DEFAULT 0")

    theme_columns = {row[1] for row in conn.execute("PRAGMA table_info(themes)")}
    if "excluded" not in theme_columns:
        conn.execute("ALTER TABLE themes ADD COLUMN excluded INTEGER NOT NULL DEFAULT 0")
    if "is_main" not in theme_columns:
        conn.execute("ALTER TABLE themes ADD COLUMN is_main INTEGER NOT NULL DEFAULT 0")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_themes_is_main ON themes(is_main) WHERE is_main = 1")

    _migrate_segment_styles_check(conn)
    _migrate_theme_subplot_model(conn)
    _migrate_drop_subplot_title_summary(conn)

    conn.commit()


def _migrate_segment_styles_check(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'segment_styles'"
    ).fetchone()
    if row is None or "'heading'" in row[0]:
        return

    # SQLite can't alter a CHECK constraint in place, so rebuild the table.
    conn.execute("ALTER TABLE segment_styles RENAME TO segment_styles_old")
    conn.execute("DROP INDEX IF EXISTS idx_segment_styles_segment")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute("INSERT INTO segment_styles SELECT * FROM segment_styles_old")
    conn.execute("DROP TABLE segment_styles_old")


def _migrate_theme_subplot_model(conn: sqlite3.Connection) -> None:
    # Ensure the Main theme exists - always, whether this is a brand-new
    # database (schema.sql already has the tightened constraints, nothing
    # else to migrate) or an old one being upgraded below.
    main_row = conn.execute("SELECT id FROM themes WHERE is_main = 1").fetchone()
    if main_row is None:
        cursor = conn.execute(
            "INSERT INTO themes (title, summary, is_main, excluded, created_at) VALUES (?, ?, 1, 0, ?)",
            (
                "Main",
                "The main plot: everything not part of a more specific subplot.",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        main_theme_id = cursor.lastrowid
    else:
        main_theme_id = main_row["id"]

    topic_info = {row[1]: row for row in conn.execute("PRAGMA table_info(topics)").fetchall()}
    if topic_info["theme_id"][3] == 1:
        return  # theme_id already NOT NULL: already fully migrated

    # Every topic must end up with a theme: fold in anything the LLM left
    # ungrouped, then fold in whatever the old subplot_topics join table
    # said before that mechanism is retired in favor of theme_id alone.
    conn.execute("UPDATE topics SET theme_id = ? WHERE theme_id IS NULL", (main_theme_id,))

    subplot_topics_exists = (
        conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'subplot_topics'").fetchone()
        is not None
    )
    if subplot_topics_exists:
        for row in conn.execute(
            """
            SELECT subplot_topics.topic_id AS topic_id, subplots.theme_id AS theme_id
            FROM subplot_topics
            JOIN subplots ON subplots.id = subplot_topics.subplot_id
            """
        ).fetchall():
            conn.execute("UPDATE topics SET theme_id = ? WHERE id = ?", (row["theme_id"], row["topic_id"]))
        conn.execute("DROP TABLE subplot_topics")

    # Retire any theme (other than Main) that has no active topics left -
    # leftovers from a superseded reanalyze pass, or a manually-created
    # subplot that was never populated. Its excluded topics move to Main
    # first so nothing is left pointing at a theme about to be deleted.
    for row in conn.execute(
        """
        SELECT id FROM themes
        WHERE is_main = 0
        AND NOT EXISTS (SELECT 1 FROM topics WHERE topics.theme_id = themes.id AND topics.excluded = 0)
        """
    ).fetchall():
        theme_id = row["id"]
        conn.execute("UPDATE topics SET theme_id = ? WHERE theme_id = ?", (main_theme_id, theme_id))
        conn.execute("DELETE FROM subplots WHERE theme_id = ?", (theme_id,))
        conn.execute("DELETE FROM themes WHERE id = ?", (theme_id,))

    # Every surviving non-Main theme must have exactly one subplot.
    now = datetime.now(timezone.utc).isoformat()
    for row in conn.execute(
        """
        SELECT id, title, summary FROM themes
        WHERE is_main = 0 AND NOT EXISTS (SELECT 1 FROM subplots WHERE subplots.theme_id = themes.id)
        """
    ).fetchall():
        conn.execute(
            "INSERT INTO subplots (theme_id, title, summary, created_at) VALUES (?, ?, ?, ?)",
            (row["id"], row["title"], row["summary"], now),
        )

    # SQLite can't add NOT NULL/UNIQUE to an existing column, so rebuild
    # topics and subplots with the tightened constraints. Column names are
    # listed explicitly on both sides: `act` and `excluded` were added to
    # topics via ALTER TABLE ADD COLUMN over this database's history, which
    # appends them at the physical end regardless of where schema.sql
    # declares them, so a bare `SELECT *` would silently shift values into
    # the wrong columns.
    conn.execute("ALTER TABLE topics RENAME TO topics_old")
    conn.execute("DROP INDEX IF EXISTS idx_topics_document_sequence")
    conn.execute("ALTER TABLE subplots RENAME TO subplots_old")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        """
        INSERT INTO topics
            (id, document_id, theme_id, act, sequence_index, title, summary,
             segment_start_id, segment_end_id, excluded, created_at)
        SELECT id, document_id, theme_id, act, sequence_index, title, summary,
               segment_start_id, segment_end_id, excluded, created_at
        FROM topics_old
        """
    )
    conn.execute(
        """
        INSERT INTO subplots (id, theme_id, title, summary, created_at)
        SELECT id, theme_id, title, summary, created_at FROM subplots_old
        """
    )
    conn.execute("DROP TABLE topics_old")
    conn.execute("DROP TABLE subplots_old")


def _migrate_drop_subplot_title_summary(conn: sqlite3.Connection) -> None:
    subplot_columns = {row[1] for row in conn.execute("PRAGMA table_info(subplots)")}
    if "title" not in subplot_columns:
        return  # already migrated, or a fresh database whose schema.sql never had these columns

    # A subplot's title/summary used to be its own copy, taken from its theme
    # at creation time - now that every subplot is permanently 1:1 with a
    # theme, that copy is dropped in favor of always reading the theme's.
    conn.execute("ALTER TABLE subplots RENAME TO subplots_old")
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute(
        "INSERT INTO subplots (id, theme_id, created_at) SELECT id, theme_id, created_at FROM subplots_old"
    )
    conn.execute("DROP TABLE subplots_old")


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

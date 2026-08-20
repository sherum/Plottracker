import sqlite3
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
    topic_columns = {row[1] for row in conn.execute("PRAGMA table_info(topics)")}
    if "act" not in topic_columns:
        conn.execute("ALTER TABLE topics ADD COLUMN act TEXT CHECK (act IN ('opening', 'conflict', 'climax'))")
    if "excluded" not in topic_columns:
        conn.execute("ALTER TABLE topics ADD COLUMN excluded INTEGER NOT NULL DEFAULT 0")

    theme_columns = {row[1] for row in conn.execute("PRAGMA table_info(themes)")}
    if "excluded" not in theme_columns:
        conn.execute("ALTER TABLE themes ADD COLUMN excluded INTEGER NOT NULL DEFAULT 0")

    _migrate_segment_styles_check(conn)

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


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

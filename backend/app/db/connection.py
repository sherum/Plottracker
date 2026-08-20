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

    conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

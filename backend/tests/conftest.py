import sqlite3

import pytest

from app.db.connection import get_connection


@pytest.fixture
def db_conn(tmp_path) -> sqlite3.Connection:
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()

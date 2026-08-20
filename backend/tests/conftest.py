import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db.connection import get_connection, get_db
from app.main import app


@pytest.fixture
def db_conn(tmp_path) -> sqlite3.Connection:
    conn = get_connection(tmp_path / "test.db")
    yield conn
    conn.close()


@pytest.fixture
def client(db_conn):
    def override_get_db():
        yield db_conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

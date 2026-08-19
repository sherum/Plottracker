import pytest
from fastapi.testclient import TestClient

from app.db.connection import get_db
from app.main import app


@pytest.fixture
def client(db_conn):
    def override_get_db():
        yield db_conn

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_and_query_documents(client, tmp_path):
    (tmp_path / "notes.txt").write_text("First paragraph.\n\nSecond paragraph.")

    response = client.post("/ingest", json={"folder_path": str(tmp_path), "role": "story_note"})
    assert response.status_code == 200
    assert response.json()["ingested"] == ["notes.txt"]

    documents_response = client.get("/documents")
    assert documents_response.status_code == 200
    documents = documents_response.json()
    assert len(documents) == 1
    assert documents[0]["filename"] == "notes.txt"

    segments_response = client.get(f"/documents/{documents[0]['id']}/segments")
    assert segments_response.status_code == 200
    segments = segments_response.json()
    assert [s["text"] for s in segments] == ["First paragraph.", "Second paragraph."]

from app.db import repository
from app.db.stories import assign_story


def _document(db_conn, filename):
    document_id = repository.insert_document(
        db_conn, role="draft_script", source_path=f"/tmp/{filename}", filename=filename, source_type="docx",
        content_hash=filename,
    )
    assign_story(db_conn, document_id)
    return document_id


def _story(db_conn, document_id):
    return repository.get_document(db_conn, document_id)["story_id"]


def test_stories_list_their_names_in_order(client, db_conn):
    _document(db_conn, "alpha_1.docx")

    stories = client.get("/stories").json()

    assert [(s["name"], s["names"]) for s in stories] == [("alpha", ["alpha"])]


def test_link_endpoint_merges_two_stories_in_the_requested_order(client, db_conn):
    a = _document(db_conn, "alpha.docx")
    b = _document(db_conn, "beta.docx")

    response = client.post(
        "/stories/link", json={"first_story_id": _story(db_conn, b), "second_story_id": _story(db_conn, a)}
    )

    assert response.status_code == 200
    survivor = response.json()["story_id"]
    stories = client.get("/stories").json()
    assert [(s["id"], s["names"], s["document_count"]) for s in stories] == [(survivor, ["beta", "alpha"], 2)]
    assert [d["filename"] for d in client.get(f"/story/documents?story_id={survivor}").json()] == [
        "beta.docx",
        "alpha.docx",
    ]


def test_linking_a_story_to_itself_is_rejected(client, db_conn):
    story = _story(db_conn, _document(db_conn, "alpha.docx"))

    response = client.post("/stories/link", json={"first_story_id": story, "second_story_id": story})

    assert response.status_code == 400


def test_unlink_endpoint_splits_the_last_story_back_out(client, db_conn):
    a = _document(db_conn, "alpha.docx")
    b = _document(db_conn, "beta.docx")
    linked = client.post(
        "/stories/link", json={"first_story_id": _story(db_conn, a), "second_story_id": _story(db_conn, b)}
    ).json()["story_id"]

    response = client.post(f"/stories/{linked}/unlink")

    assert response.status_code == 200
    assert sorted(s["names"][0] for s in client.get("/stories").json()) == ["alpha", "beta"]
    assert response.json()["story_id"] == _story(db_conn, b)


def test_unlinking_an_unlinked_story_is_rejected(client, db_conn):
    story = _story(db_conn, _document(db_conn, "alpha.docx"))

    assert client.post(f"/stories/{story}/unlink").status_code == 400

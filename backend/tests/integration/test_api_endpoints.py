from app.analysis import llm
from app.analysis.models import AnalysisResult, ThemeOut, TopicOut
from app.db import repository
from app.ingest import service as ingest_service
from app.sidekick import llm as sidekick_llm


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_subplots_document_id_query_param(client, db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Text.")
    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=segment_id,
        segment_end_id=segment_id,
    )
    subplot_id = repository.insert_subplot(db_conn, title="A Subplot", summary="Summary.", theme_id=theme_id)
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_id)

    other_document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter2.txt",
        filename="chapter2.txt",
        source_type="txt",
        content_hash="hash2",
    )

    assert [s["id"] for s in client.get(f"/subplots?document_id={document_id}").json()] == [subplot_id]
    assert client.get(f"/subplots?document_id={other_document_id}").json() == []
    assert [s["id"] for s in client.get("/subplots").json()] == [subplot_id]


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

    delete_response = client.delete(f"/documents/{documents[0]['id']}")
    assert delete_response.status_code == 200
    assert client.get("/documents").json() == []


def test_ingest_missing_folder_returns_400(client, tmp_path):
    response = client.post("/ingest", json={"folder_path": str(tmp_path / "nope"), "role": "draft_script"})
    assert response.status_code == 400


def test_ingest_upload_creates_document(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_service, "REPO_ROOT", tmp_path)

    response = client.post(
        "/ingest/upload",
        files={"file": ("notes.txt", b"First paragraph.\n\nSecond paragraph.", "text/plain")},
        data={"role": "story_note"},
    )
    assert response.status_code == 200
    assert response.json() == {"ingested": ["notes.txt"], "skipped": [], "failed": []}
    assert (tmp_path / "story_notes" / "notes.txt").exists()

    documents = client.get("/documents").json()
    assert documents[0]["filename"] == "notes.txt"


def test_rename_document_moves_file_and_updates_filename(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_service, "REPO_ROOT", tmp_path)
    client.post(
        "/ingest/upload",
        files={"file": ("notes.txt", b"First paragraph.\n\nSecond paragraph.", "text/plain")},
        data={"role": "story_note"},
    )
    document_id = client.get("/documents").json()[0]["id"]

    response = client.patch(f"/documents/{document_id}", json={"filename": "renamed.txt"})
    assert response.status_code == 200
    assert response.json()["filename"] == "renamed.txt"

    assert not (tmp_path / "story_notes" / "notes.txt").exists()
    assert (tmp_path / "story_notes" / "renamed.txt").read_text() == "First paragraph.\n\nSecond paragraph."
    assert client.get("/documents").json()[0]["filename"] == "renamed.txt"


def test_rename_document_rejects_name_collision(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_service, "REPO_ROOT", tmp_path)
    client.post(
        "/ingest/upload",
        files={"file": ("notes.txt", b"Text.", "text/plain")},
        data={"role": "story_note"},
    )
    client.post(
        "/ingest/upload",
        files={"file": ("other.txt", b"Other text.", "text/plain")},
        data={"role": "story_note"},
    )
    documents = client.get("/documents").json()
    notes_id = next(d["id"] for d in documents if d["filename"] == "notes.txt")

    response = client.patch(f"/documents/{notes_id}", json={"filename": "other.txt"})

    assert response.status_code == 400


def test_ingest_upload_skips_unsupported_extension(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_service, "REPO_ROOT", tmp_path)

    response = client.post(
        "/ingest/upload",
        files={"file": ("notes.xyz", b"whatever", "application/octet-stream")},
        data={"role": "draft_script"},
    )
    assert response.status_code == 200
    assert response.json() == {"ingested": [], "skipped": ["notes.xyz"], "failed": []}


def test_ingest_upload_unknown_role_returns_400(client, tmp_path, monkeypatch):
    monkeypatch.setattr(ingest_service, "REPO_ROOT", tmp_path)

    response = client.post(
        "/ingest/upload",
        files={"file": ("notes.txt", b"text", "text/plain")},
        data={"role": "not_a_real_role"},
    )
    assert response.status_code == 400


def test_analyze_document_creates_topics_and_themes(client, db_conn, tmp_path, monkeypatch):
    (tmp_path / "chapter1.txt").write_text("The hero leaves home.\n\nThe hero finds an ally.")
    client.post("/ingest", json={"folder_path": str(tmp_path), "role": "draft_script"})
    document_id = client.get("/documents").json()[0]["id"]
    segment_ids = [s["id"] for s in client.get(f"/documents/{document_id}/segments").json()]

    fake_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[0],
                segment_end_id=segment_ids[0],
                title="Departure",
                summary="The hero leaves home.",
                act="opening",
            )
        ],
        themes=[ThemeOut(title="Journey", summary="The hero's journey begins.", topic_indices=[0])],
    )
    monkeypatch.setattr(llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

    analyze_response = client.post(f"/documents/{document_id}/analyze")
    assert analyze_response.status_code == 200
    assert analyze_response.json() == {"topics_created": 1, "themes_created": 1}

    topics = client.get(f"/documents/{document_id}/topics").json()
    assert topics[0]["title"] == "Departure"

    themes = client.get("/themes").json()
    journey_theme = next(t for t in themes if t["title"] == "Journey")

    all_topics = client.get("/topics").json()
    assert all_topics[0]["title"] == "Departure"
    assert all_topics[0]["document_filename"] == "chapter1.txt"

    topic_id = all_topics[0]["id"]
    patch_topic_response = client.patch(
        f"/topics/{topic_id}", json={"title": "Departure (revised)", "summary": "Updated summary."}
    )
    assert patch_topic_response.status_code == 200
    assert patch_topic_response.json()["title"] == "Departure (revised)"
    assert client.get(f"/documents/{document_id}/topics").json()[0]["summary"] == "Updated summary."

    theme_id = journey_theme["id"]
    patch_theme_response = client.patch(
        f"/themes/{theme_id}", json={"title": "Journey (revised)", "summary": "Updated theme summary."}
    )
    assert patch_theme_response.status_code == 200
    assert patch_theme_response.json()["title"] == "Journey (revised)"
    updated_theme = next(t for t in client.get("/themes").json() if t["id"] == theme_id)
    assert updated_theme["summary"] == "Updated theme summary."

    # analyze already auto-created a subplot for this theme - no manual promotion step.
    subplots = client.get("/subplots").json()
    subplot = next(s for s in subplots if s["theme_id"] == theme_id)
    assert subplot["topic_count"] == 1

    manual_subplot = client.post("/subplots", json={"title": "Author's Subplot", "summary": "Manual."}).json()
    assert manual_subplot["topic_count"] == 0

    add_response = client.post(f"/subplots/{manual_subplot['id']}/topics", json={"topic_id": topic_id})
    assert add_response.status_code == 200
    assert add_response.json()["topic_count"] == 1
    assert client.get(f"/subplots/{manual_subplot['id']}/topics").json()[0]["id"] == topic_id

    remove_response = client.delete(f"/subplots/{manual_subplot['id']}/topics/{topic_id}")
    assert remove_response.status_code == 200
    assert remove_response.json()["topic_count"] == 0

    delete_subplot_response = client.delete(f"/subplots/{manual_subplot['id']}")
    assert delete_subplot_response.status_code == 200
    assert delete_subplot_response.json() == {"deleted": manual_subplot["id"]}
    assert manual_subplot["id"] not in [s["id"] for s in client.get("/subplots").json()]

    monkeypatch.setattr(
        sidekick_llm,
        "answer_question",
        lambda conn, question, topics, themes, encoding_rules, subplots, **kwargs: (
            "Because reasons.",
            [],
            None,
            None,
        ),
    )
    ask_response = client.post(
        "/sidekick/ask",
        json={"question": "Why?", "topic_ids": [topic_id], "current_topic_id": topic_id, "current_theme_id": theme_id},
    )
    assert ask_response.status_code == 200
    assert ask_response.json() == {
        "answer": "Because reasons.",
        "actions": [],
        "created_subplot_id": None,
        "filtered_topic_ids": None,
    }

    source_text_response = client.get(f"/topics/{topic_id}/source-text")
    assert source_text_response.status_code == 200
    assert source_text_response.json() == {"text": "The hero leaves home."}

    exclude_response = client.post(f"/topics/{topic_id}/exclude")
    assert exclude_response.status_code == 200
    assert exclude_response.json()["excluded"] == 1

    captured = {}
    monkeypatch.setattr(
        sidekick_llm,
        "answer_question",
        lambda conn, question, topics, themes, encoding_rules, subplots, **kwargs: (
            captured.update(topics=topics) or "n/a",
            [],
            None,
            None,
        ),
    )
    client.post("/sidekick/ask", json={"question": "Why?", "topic_ids": [topic_id]})
    assert captured["topics"] == []

    include_response = client.post(f"/topics/{topic_id}/include")
    assert include_response.status_code == 200
    assert include_response.json()["excluded"] == 0

    unassign_response = client.post(f"/topics/{topic_id}/unassign-theme")
    assert unassign_response.status_code == 200
    story_id = repository.get_document(db_conn, document_id)["story_id"]
    assert unassign_response.json()["theme_id"] == repository.get_main_theme_id(db_conn, story_id)

    set_act_response = client.post(f"/topics/{topic_id}/set-act", json={"act": "climax"})
    assert set_act_response.status_code == 200
    assert set_act_response.json()["act"] == "climax"

    clear_act_response = client.post(f"/topics/{topic_id}/set-act", json={"act": None})
    assert clear_act_response.status_code == 200
    assert clear_act_response.json()["act"] is None

    move_response = client.post(f"/topics/{topic_id}/move", json={"theme_id": theme_id, "act": "opening"})
    assert move_response.status_code == 200
    assert move_response.json()["theme_id"] == theme_id
    assert move_response.json()["act"] == "opening"

    exclude_theme_response = client.post(f"/themes/{theme_id}/exclude")
    assert exclude_theme_response.status_code == 200
    assert exclude_theme_response.json()["excluded"] == 1


def test_split_topic_endpoint(client, db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    seg1 = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="First.")
    seg2 = repository.insert_segment(db_conn, document_id=document_id, sequence_index=1, text="Second.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=seg1,
        segment_end_id=seg2,
    )

    segments_response = client.get(f"/topics/{topic_id}/segments")
    assert segments_response.status_code == 200
    assert [s["text"] for s in segments_response.json()] == ["First.", "Second."]

    split_response = client.post(f"/topics/{topic_id}/split", json={"split_segment_id": seg2})
    assert split_response.status_code == 200
    body = split_response.json()
    assert body["original"]["segment_end_id"] == seg1
    assert body["new"]["segment_start_id"] == seg2
    assert body["new"]["sequence_index"] == 1

    topics = client.get(f"/documents/{document_id}/topics").json()
    assert len(topics) == 2


def test_set_main_theme_endpoint(client, db_conn):
    old_main_id = repository.get_main_theme_id(db_conn)
    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    repository.insert_subplot(db_conn, theme_id=theme_id)

    response = client.post(f"/themes/{theme_id}/set-main")
    assert response.status_code == 200
    assert response.json()["is_main"] == 1

    assert repository.get_main_theme_id(db_conn) == theme_id
    assert any(s["theme_id"] == old_main_id for s in client.get("/subplots").json())


def test_story_order_can_be_reordered_and_reset(client, db_conn):
    from app.db.stories import assign_story

    doc_1 = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/saga_1.txt", filename="saga_1.txt", source_type="txt", content_hash="1"
    )
    doc_2 = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/saga_2.txt", filename="saga_2.txt", source_type="txt", content_hash="2"
    )
    assign_story(db_conn, doc_1)
    assign_story(db_conn, doc_2)

    assert [d["id"] for d in client.get("/story/documents").json()] == [doc_1, doc_2]

    put_response = client.put("/story/documents", json={"document_ids": [doc_2, doc_1]})
    assert put_response.status_code == 200
    assert [d["id"] for d in put_response.json()] == [doc_2, doc_1]

    story_id = repository.get_document(db_conn, doc_1)["story_id"]
    reset_response = client.put("/story/documents", json={"document_ids": [], "story_id": story_id})
    assert reset_response.status_code == 200
    assert [d["id"] for d in client.get("/story/documents").json()] == [doc_1, doc_2]


def test_encoding_rule_crud(client):
    create_response = client.post(
        "/encoding-rules",
        json={
            "style_kind": "italic",
            "block_length": "multi",
            "position": "chapter_start",
            "label": "dream_sequence",
            "description": "Original.",
        },
    )
    assert create_response.status_code == 200
    rule_id = create_response.json()["id"]

    assert client.get("/encoding-rules").json()[0]["label"] == "dream_sequence"

    update_response = client.patch(
        f"/encoding-rules/{rule_id}",
        json={
            "style_kind": "bold",
            "block_length": "single",
            "position": "anywhere",
            "label": "renamed_rule",
            "description": "Revised.",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "renamed_rule"
    assert client.get("/encoding-rules").json()[0]["style_kind"] == "bold"

    delete_response = client.delete(f"/encoding-rules/{rule_id}")
    assert delete_response.status_code == 200
    assert client.get("/encoding-rules").json() == []


def test_encoding_rule_enabled_toggle_is_scoped_to_document(client, db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    other_document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter2.txt",
        filename="chapter2.txt",
        source_type="txt",
        content_hash="hash2",
    )
    rule_id = repository.insert_encoding_rule(
        db_conn, style_kind="italic", block_length="multi", position="chapter_start", label="dream_sequence"
    )

    scoped = client.get("/encoding-rules", params={"document_id": document_id}).json()
    assert scoped[0]["enabled"] == 1

    toggle_response = client.patch(f"/documents/{document_id}/encoding-rules/{rule_id}", json={"enabled": False})
    assert toggle_response.status_code == 200
    assert toggle_response.json() == {"document_id": document_id, "id": rule_id, "enabled": False}

    assert client.get("/encoding-rules", params={"document_id": document_id}).json()[0]["enabled"] == 0
    assert client.get("/encoding-rules", params={"document_id": other_document_id}).json()[0]["enabled"] == 1

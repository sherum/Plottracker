from app.analysis import llm
from app.analysis.models import AnalysisResult, ThemeOut, TopicOut
from app.sidekick import llm as sidekick_llm


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


def test_ingest_missing_folder_returns_400(client, tmp_path):
    response = client.post("/ingest", json={"folder_path": str(tmp_path / "nope"), "role": "draft_script"})
    assert response.status_code == 400


def test_analyze_document_creates_topics_and_themes(client, tmp_path, monkeypatch):
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
    monkeypatch.setattr(llm, "extract_topics_and_themes", lambda segments: fake_result)

    analyze_response = client.post(f"/documents/{document_id}/analyze")
    assert analyze_response.status_code == 200
    assert analyze_response.json() == {"topics_created": 1, "themes_created": 1}

    topics = client.get(f"/documents/{document_id}/topics").json()
    assert topics[0]["title"] == "Departure"

    themes = client.get("/themes").json()
    assert themes[0]["title"] == "Journey"

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

    theme_id = themes[0]["id"]
    patch_theme_response = client.patch(
        f"/themes/{theme_id}", json={"title": "Journey (revised)", "summary": "Updated theme summary."}
    )
    assert patch_theme_response.status_code == 200
    assert patch_theme_response.json()["title"] == "Journey (revised)"
    assert client.get("/themes").json()[0]["summary"] == "Updated theme summary."

    promote_response = client.post(f"/themes/{theme_id}/promote")
    assert promote_response.status_code == 200
    subplot = promote_response.json()
    assert subplot["theme_id"] == theme_id
    assert subplot["topic_count"] == 1

    subplots = client.get("/subplots").json()
    assert subplots[0]["id"] == subplot["id"]

    manual_subplot = client.post("/subplots", json={"title": "Author's Subplot", "summary": "Manual."}).json()
    assert manual_subplot["topic_count"] == 0

    add_response = client.post(f"/subplots/{manual_subplot['id']}/topics", json={"topic_id": topic_id})
    assert add_response.status_code == 200
    assert add_response.json()["topic_count"] == 1
    assert client.get(f"/subplots/{manual_subplot['id']}/topics").json()[0]["id"] == topic_id

    remove_response = client.delete(f"/subplots/{manual_subplot['id']}/topics/{topic_id}")
    assert remove_response.status_code == 200
    assert remove_response.json()["topic_count"] == 0

    monkeypatch.setattr(sidekick_llm, "answer_question", lambda question, topics, themes: "Because reasons.")
    ask_response = client.post("/sidekick/ask", json={"question": "Why?", "topic_ids": [topic_id]})
    assert ask_response.status_code == 200
    assert ask_response.json() == {"answer": "Because reasons."}

    exclude_response = client.post(f"/topics/{topic_id}/exclude")
    assert exclude_response.status_code == 200
    assert exclude_response.json()["excluded"] == 1

    captured = {}
    monkeypatch.setattr(
        sidekick_llm,
        "answer_question",
        lambda question, topics, themes: captured.update(topics=topics) or "n/a",
    )
    client.post("/sidekick/ask", json={"question": "Why?", "topic_ids": [topic_id]})
    assert captured["topics"] == []

    include_response = client.post(f"/topics/{topic_id}/include")
    assert include_response.status_code == 200
    assert include_response.json()["excluded"] == 0

    exclude_theme_response = client.post(f"/themes/{theme_id}/exclude")
    assert exclude_theme_response.status_code == 200
    assert exclude_theme_response.json()["excluded"] == 1

from app.db import repository
from app.sidekick import llm, service


def _make_document_with_topics(db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Text.")
    theme_id = repository.insert_theme(db_conn, title="Ties to the Past", summary="A recurring thread.")
    topic_ids = [
        repository.insert_topic(
            db_conn,
            document_id=document_id,
            sequence_index=i,
            title=title,
            summary=title,
            segment_start_id=segment_id,
            segment_end_id=segment_id,
            act="opening",
        )
        for i, title in enumerate(["First topic", "Second topic"])
    ]
    repository.set_topic_theme(db_conn, topic_ids[0], theme_id)
    return theme_id, topic_ids


def test_ask_scopes_context_to_given_topic_ids(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)

    captured = {}

    def fake_answer_question(question, topics, themes):
        captured["question"] = question
        captured["topics"] = topics
        captured["themes"] = themes
        return "The answer."

    monkeypatch.setattr(llm, "answer_question", fake_answer_question)

    answer = service.ask(db_conn, "What happens first?", [topic_ids[0]])

    assert answer == "The answer."
    assert captured["question"] == "What happens first?"
    assert [t["title"] for t in captured["topics"]] == ["First topic"]
    assert [t["id"] for t in captured["themes"]] == [theme_id]

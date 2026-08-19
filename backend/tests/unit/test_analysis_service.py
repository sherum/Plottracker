from app.analysis import service
from app.analysis.models import AnalysisResult, ThemeOut, TopicOut
from app.db import repository


def _make_document_with_segments(db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    segment_ids = [
        repository.insert_segment(db_conn, document_id=document_id, sequence_index=i, text=text)
        for i, text in enumerate(["The hero leaves home.", "The hero finds an ally."])
    ]
    return document_id, segment_ids


def test_analyze_document_stores_topics_and_themes(db_conn, monkeypatch):
    document_id, segment_ids = _make_document_with_segments(db_conn)

    fake_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[0],
                segment_end_id=segment_ids[0],
                title="Departure",
                summary="The hero leaves home.",
            ),
            TopicOut(
                segment_start_id=segment_ids[1],
                segment_end_id=segment_ids[1],
                title="New Ally",
                summary="The hero finds an ally.",
            ),
        ],
        themes=[ThemeOut(title="Journey", summary="The hero's journey begins.", topic_indices=[0, 1])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: fake_result)

    summary = service.analyze_document(db_conn, document_id)

    assert summary == {"topics_created": 2, "themes_created": 1}

    topics = repository.list_topics(db_conn, document_id)
    assert [t["title"] for t in topics] == ["Departure", "New Ally"]

    themes = repository.list_themes(db_conn)
    assert len(themes) == 1
    assert all(t["theme_id"] == themes[0]["id"] for t in topics)


def test_analyze_document_without_segments_raises(db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/empty.txt",
        filename="empty.txt",
        source_type="txt",
        content_hash="hash",
    )

    try:
        service.analyze_document(db_conn, document_id)
        assert False, "expected ValueError"
    except ValueError:
        pass

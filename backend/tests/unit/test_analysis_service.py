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
                act="opening",
            ),
            TopicOut(
                segment_start_id=segment_ids[1],
                segment_end_id=segment_ids[1],
                title="New Ally",
                summary="The hero finds an ally.",
                act="opening",
            ),
        ],
        themes=[ThemeOut(title="Journey", summary="The hero's journey begins.", topic_indices=[0, 1])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: fake_result)

    summary = service.analyze_document(db_conn, document_id)

    assert summary == {"topics_created": 2, "themes_created": 1}

    topics = repository.list_topics(db_conn, document_id)
    assert [t["title"] for t in topics] == ["Departure", "New Ally"]
    assert all(t["act"] == "opening" for t in topics)

    themes = repository.list_themes(db_conn)
    assert len(themes) == 1
    assert all(t["theme_id"] == themes[0]["id"] for t in topics)


def test_reanalyze_excludes_old_topics_instead_of_duplicating(db_conn, monkeypatch):
    document_id, segment_ids = _make_document_with_segments(db_conn)

    first_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[0],
                segment_end_id=segment_ids[0],
                title="Departure (first pass)",
                summary="The hero leaves home.",
                act="opening",
            )
        ],
        themes=[],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: first_result)
    service.analyze_document(db_conn, document_id)

    second_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[0],
                segment_end_id=segment_ids[0],
                title="Departure (revised pass)",
                summary="The hero leaves home, reluctantly.",
                act="opening",
            )
        ],
        themes=[],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: second_result)
    service.analyze_document(db_conn, document_id)

    topics = repository.list_topics(db_conn, document_id)
    assert len(topics) == 2
    first_pass = next(t for t in topics if t["title"] == "Departure (first pass)")
    second_pass = next(t for t in topics if t["title"] == "Departure (revised pass)")
    assert first_pass["excluded"] == 1
    assert second_pass["excluded"] == 0


def test_analyze_document_trims_topic_ending_on_next_chapter_heading(db_conn, monkeypatch):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    heading_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Chapter One")
    prose_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=1, text="The hero leaves home.")
    next_heading_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=2, text="Chapter Two")
    repository.insert_style(db_conn, segment_id=heading_id, style_kind="heading")
    repository.insert_style(db_conn, segment_id=next_heading_id, style_kind="heading")

    fake_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=heading_id,
                segment_end_id=next_heading_id,
                title="Departure",
                summary="The hero leaves home.",
                act="opening",
            )
        ],
        themes=[],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: fake_result)

    service.analyze_document(db_conn, document_id)

    topics = repository.list_topics(db_conn, document_id)
    assert topics[0]["segment_end_id"] == prose_id


def test_analyze_document_keeps_single_segment_heading_topic_untrimmed(db_conn, monkeypatch):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    heading_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Chapter One")
    repository.insert_style(db_conn, segment_id=heading_id, style_kind="heading")

    fake_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=heading_id,
                segment_end_id=heading_id,
                title="Chapter opener",
                summary="Just the heading.",
                act="opening",
            )
        ],
        themes=[],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments: fake_result)

    service.analyze_document(db_conn, document_id)

    topics = repository.list_topics(db_conn, document_id)
    assert topics[0]["segment_end_id"] == heading_id


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

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
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

    summary = service.analyze_document(db_conn, document_id)

    assert summary == {"topics_created": 2, "themes_created": 1}

    topics = repository.list_topics(db_conn, document_id)
    assert [t["title"] for t in topics] == ["Departure", "New Ally"]
    assert all(t["act"] == "opening" for t in topics)

    main_theme_id = repository.get_main_theme_id(db_conn)
    non_main_themes = [t for t in repository.list_themes(db_conn) if t["id"] != main_theme_id]
    assert len(non_main_themes) == 1
    theme_id = non_main_themes[0]["id"]
    assert all(t["theme_id"] == theme_id for t in topics)

    # A subplot is created automatically - no manual promotion step.
    subplots = repository.list_subplots(db_conn, document_id)
    assert len(subplots) == 1
    assert subplots[0]["theme_id"] == theme_id
    assert subplots[0]["topic_count"] == 2


def test_analyze_document_leaves_ungrouped_topics_under_main(db_conn, monkeypatch):
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
                title="An unrelated aside",
                summary="Not part of any thread.",
                act="opening",
            ),
        ],
        # Only the first topic is grouped into a theme; the second is left out entirely.
        themes=[ThemeOut(title="Journey", summary="The hero's journey begins.", topic_indices=[0])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

    service.analyze_document(db_conn, document_id)

    main_theme_id = repository.get_main_theme_id(db_conn)
    topics = {t["title"]: t for t in repository.list_topics(db_conn, document_id)}
    assert topics["An unrelated aside"]["theme_id"] == main_theme_id
    assert topics["Departure"]["theme_id"] != main_theme_id


def test_analyze_document_caps_auto_created_subplots_at_four(db_conn, monkeypatch):
    document_id, _ = _make_document_with_segments(db_conn)
    # 6 themes of decreasing size; only the top 4 by topic count should get a subplot.
    sizes = [5, 4, 3, 2, 1, 1]
    total_topics = sum(sizes)
    segment_ids = [
        repository.insert_segment(db_conn, document_id=document_id, sequence_index=i, text=f"Sentence {i}.")
        for i in range(2, 2 + total_topics)
    ]

    topics = [
        TopicOut(
            segment_start_id=segment_ids[i],
            segment_end_id=segment_ids[i],
            title=f"Topic {i}",
            summary="s",
            act="opening",
        )
        for i in range(total_topics)
    ]
    themes = []
    cursor = 0
    for i, size in enumerate(sizes):
        themes.append(
            ThemeOut(title=f"Theme {i}", summary="s", topic_indices=list(range(cursor, cursor + size)))
        )
        cursor += size
    fake_result = AnalysisResult(topics=topics, themes=themes)
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

    summary = service.analyze_document(db_conn, document_id)

    assert summary["themes_created"] == 4
    main_theme_id = repository.get_main_theme_id(db_conn)
    non_main_themes = [t for t in repository.list_themes(db_conn) if t["id"] != main_theme_id]
    assert {t["title"] for t in non_main_themes} == {"Theme 0", "Theme 1", "Theme 2", "Theme 3"}

    # The two smallest themes (size 1 each) never became subplots - their
    # topics stayed under Main instead.
    all_topics = repository.list_topics(db_conn, document_id)
    main_topic_titles = {t["title"] for t in all_topics if t["theme_id"] == main_theme_id}
    assert main_topic_titles == {"Topic 14", "Topic 15"}


def test_analyze_document_ignores_out_of_range_topic_indices(db_conn, monkeypatch):
    document_id, segment_ids = _make_document_with_segments(db_conn)

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
        themes=[ThemeOut(title="Journey", summary="s", topic_indices=[0, 5, -1])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

    summary = service.analyze_document(db_conn, document_id)

    assert summary == {"topics_created": 1, "themes_created": 1}
    topic = repository.list_topics(db_conn, document_id)[0]
    main_theme_id = repository.get_main_theme_id(db_conn)
    assert topic["theme_id"] != main_theme_id


def test_reanalyze_keeps_theme_that_loses_its_last_topic(db_conn, monkeypatch):
    document_id, segment_ids = _make_document_with_segments(db_conn)

    first_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[0],
                segment_end_id=segment_ids[0],
                title="Departure",
                summary="The hero leaves home.",
                act="opening",
            )
        ],
        themes=[ThemeOut(title="Journey", summary="s", topic_indices=[0])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: first_result)
    service.analyze_document(db_conn, document_id)

    first_pass_theme_id = next(
        t["id"] for t in repository.list_themes(db_conn) if t["title"] == "Journey"
    )
    subplot_id = repository.list_subplots(db_conn, document_id)[0]["id"]

    second_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=segment_ids[1],
                segment_end_id=segment_ids[1],
                title="A different scene",
                summary="Unrelated to the first pass.",
                act="opening",
            )
        ],
        themes=[],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: second_result)
    service.analyze_document(db_conn, document_id)

    # The theme/subplot survives even though it has no active topics left -
    # it may be manually curated, and only the user retires it.
    assert first_pass_theme_id in [t["id"] for t in repository.list_themes(db_conn)]
    assert subplot_id in [s["id"] for s in repository.list_subplots(db_conn)]


def test_analyze_document_reuses_existing_theme_when_llm_matches_one(db_conn, monkeypatch):
    first_document_id, first_segment_ids = _make_document_with_segments(db_conn)
    first_result = AnalysisResult(
        topics=[
            TopicOut(
                segment_start_id=first_segment_ids[0],
                segment_end_id=first_segment_ids[0],
                title="Departure",
                summary="The hero leaves home.",
                act="opening",
            )
        ],
        themes=[ThemeOut(title="Journey", summary="The hero's road.", topic_indices=[0])],
    )
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: first_result)
    service.analyze_document(db_conn, first_document_id)

    journey_theme_id = next(t["id"] for t in repository.list_themes(db_conn) if t["title"] == "Journey")

    second_document_id, second_segment_ids = _make_document_with_segments(db_conn)
    captured_existing_themes = {}

    def second_pass(segments, existing_themes=None):
        captured_existing_themes["value"] = existing_themes
        return AnalysisResult(
            topics=[
                TopicOut(
                    segment_start_id=second_segment_ids[0],
                    segment_end_id=second_segment_ids[0],
                    title="Further down the road",
                    summary="The hero keeps moving.",
                    act="conflict",
                )
            ],
            themes=[
                ThemeOut(
                    title="Journey",
                    summary="The hero's road.",
                    topic_indices=[0],
                    existing_theme_id=journey_theme_id,
                )
            ],
        )

    monkeypatch.setattr(service.llm, "extract_topics_and_themes", second_pass)
    summary = service.analyze_document(db_conn, second_document_id)

    # The LLM was offered the existing theme as context...
    assert captured_existing_themes["value"] == [
        {"id": journey_theme_id, "title": "Journey", "summary": "The hero's road."}
    ]
    # ...and reusing it doesn't create a duplicate or count against the cap.
    assert summary["themes_created"] == 0
    non_main_themes = [t for t in repository.list_themes(db_conn) if t["title"] == "Journey"]
    assert len(non_main_themes) == 1

    new_topic = next(
        t for t in repository.list_topics(db_conn, second_document_id) if t["title"] == "Further down the road"
    )
    assert new_topic["theme_id"] == journey_theme_id


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
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: first_result)
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
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: second_result)
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
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

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
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: fake_result)

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

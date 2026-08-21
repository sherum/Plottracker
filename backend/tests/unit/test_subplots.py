from app.db import repository


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
    return document_id, theme_id, topic_ids


def test_promote_theme_to_subplot_copies_its_topics(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)

    subplot_id = repository.promote_theme_to_subplot(db_conn, theme_id)

    subplot = repository.get_subplot(db_conn, subplot_id)
    assert subplot["theme_id"] == theme_id
    assert subplot["title"] == "Ties to the Past"
    assert subplot["topic_count"] == 1

    subplot_topics = repository.list_subplot_topics(db_conn, subplot_id)
    assert [t["id"] for t in subplot_topics] == [topic_ids[0]]


def test_manual_subplot_add_and_remove_topic(db_conn):
    _, _, topic_ids = _make_document_with_topics(db_conn)

    subplot_id = repository.insert_subplot(db_conn, title="Author's Subplot", summary="Manually created.")
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 0

    repository.add_topic_to_subplot(db_conn, subplot_id, topic_ids[1])
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 1

    repository.remove_topic_from_subplot(db_conn, subplot_id, topic_ids[1])
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 0


def test_delete_subplot_removes_subplot_and_its_topic_links(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)
    subplot_id = repository.promote_theme_to_subplot(db_conn, theme_id)

    assert repository.list_subplot_topic_ids(db_conn, subplot_id) == [topic_ids[0]]

    repository.delete_subplot(db_conn, subplot_id)

    assert subplot_id not in [s["id"] for s in repository.list_subplots(db_conn)]
    assert repository.list_subplot_topic_ids(db_conn, subplot_id) == []


def test_create_named_subplot_from_theme_has_no_topics(db_conn):
    _, theme_id, _ = _make_document_with_topics(db_conn)

    subplot_id = repository.create_named_subplot_from_theme(db_conn, theme_id, "My Subplot")

    subplot = repository.get_subplot(db_conn, subplot_id)
    assert subplot["title"] == "My Subplot"
    assert subplot["theme_id"] == theme_id
    assert subplot["topic_count"] == 0


def test_list_subplots_scoped_to_document(db_conn):
    document_id, theme_id, _ = _make_document_with_topics(db_conn)
    subplot_id = repository.promote_theme_to_subplot(db_conn, theme_id)

    other_document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter2.txt",
        filename="chapter2.txt",
        source_type="txt",
        content_hash="hash2",
    )

    assert [s["id"] for s in repository.list_subplots(db_conn, document_id)] == [subplot_id]
    assert repository.list_subplots(db_conn, other_document_id) == []
    assert [s["id"] for s in repository.list_subplots(db_conn)] == [subplot_id]


def test_list_subplots_scoped_to_document_includes_empty_named_subplot(db_conn):
    document_id, theme_id, _ = _make_document_with_topics(db_conn)
    subplot_id = repository.create_named_subplot_from_theme(db_conn, theme_id, "Empty Subplot")

    scoped = repository.list_subplots(db_conn, document_id)

    assert [s["id"] for s in scoped] == [subplot_id]


def test_get_topic_source_text_joins_segments_in_range(db_conn):
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
    seg3 = repository.insert_segment(db_conn, document_id=document_id, sequence_index=2, text="Third.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=seg1,
        segment_end_id=seg2,
    )

    text = repository.get_topic_source_text(db_conn, topic_id)

    assert text == "First.\n\nSecond."
    assert "Third." not in text

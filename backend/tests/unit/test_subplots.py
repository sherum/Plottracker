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
    main_theme_id = repository.get_main_theme_id(db_conn)
    topic_ids = [
        repository.insert_topic(
            db_conn,
            document_id=document_id,
            theme_id=main_theme_id,
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


def test_insert_subplot_without_theme_creates_one(db_conn):
    subplot_id = repository.insert_subplot(db_conn, title="Standalone Subplot", summary="No theme given.")

    subplot = repository.get_subplot(db_conn, subplot_id)
    assert subplot["theme_id"] is not None

    themes = repository.list_themes(db_conn)
    theme = next(t for t in themes if t["id"] == subplot["theme_id"])
    assert theme["title"] == "Standalone Subplot"
    assert theme["summary"] == "No theme given."


def test_insert_subplot_with_theme_reuses_it(db_conn):
    theme_id = repository.insert_theme(db_conn, title="Existing Theme", summary="Already here.")

    subplot_id = repository.insert_subplot(
        db_conn, title="Linked Subplot", summary="Uses existing theme.", theme_id=theme_id
    )

    assert repository.get_subplot(db_conn, subplot_id)["theme_id"] == theme_id
    # Main plus this one.
    assert len(repository.list_themes(db_conn)) == 2


def test_subplot_topics_are_derived_from_theme_membership(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)

    subplot_id = repository.insert_subplot(
        db_conn, title="Ties to the Past", summary="A recurring thread.", theme_id=theme_id
    )

    subplot = repository.get_subplot(db_conn, subplot_id)
    assert subplot["theme_id"] == theme_id
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


def test_remove_topic_from_subplot_sends_it_back_to_main(db_conn):
    _, _, topic_ids = _make_document_with_topics(db_conn)
    subplot_id = repository.insert_subplot(db_conn, title="Author's Subplot", summary="Manually created.")
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_ids[1])

    repository.remove_topic_from_subplot(db_conn, subplot_id, topic_ids[1])

    topic = repository.get_topics_by_ids(db_conn, [topic_ids[1]])[0]
    assert topic["theme_id"] == repository.get_main_theme_id(db_conn)


def test_delete_subplot_moves_its_topics_to_main(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)
    subplot_id = repository.insert_subplot(
        db_conn, title="Ties to the Past", summary="A recurring thread.", theme_id=theme_id
    )

    repository.delete_subplot(db_conn, subplot_id)

    assert subplot_id not in [s["id"] for s in repository.list_subplots(db_conn)]
    assert theme_id not in [t["id"] for t in repository.list_themes(db_conn)]
    topic = repository.get_topics_by_ids(db_conn, [topic_ids[0]])[0]
    assert topic["theme_id"] == repository.get_main_theme_id(db_conn)


def test_list_subplots_scoped_to_document(db_conn):
    document_id, theme_id, _ = _make_document_with_topics(db_conn)
    subplot_id = repository.insert_subplot(
        db_conn, title="Ties to the Past", summary="A recurring thread.", theme_id=theme_id
    )

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


def test_list_subplots_scoped_to_document_excludes_unpopulated_subplot(db_conn):
    document_id, _, _ = _make_document_with_topics(db_conn)
    repository.insert_subplot(db_conn, title="Empty Subplot", summary="Not yet populated.")

    assert repository.list_subplots(db_conn, document_id) == []


def test_set_story_order_assigns_sequential_positions(db_conn):
    doc_a = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/a.txt", filename="a.txt", source_type="txt", content_hash="a"
    )
    doc_b = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/b.txt", filename="b.txt", source_type="txt", content_hash="b"
    )
    doc_c = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/c.txt", filename="c.txt", source_type="txt", content_hash="c"
    )

    repository.set_story_order(db_conn, [doc_c, doc_a])

    story_documents = repository.list_story_documents(db_conn)
    assert [d["id"] for d in story_documents] == [doc_c, doc_a]
    assert [d["story_position"] for d in story_documents] == [1, 2]

    doc_b_row = next(d for d in repository.list_documents(db_conn) if d["id"] == doc_b)
    assert doc_b_row["story_position"] is None


def test_set_story_order_can_reorder_and_unlink(db_conn):
    doc_a = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/a.txt", filename="a.txt", source_type="txt", content_hash="a"
    )
    doc_b = repository.insert_document(
        db_conn, role="draft_script", source_path="/tmp/b.txt", filename="b.txt", source_type="txt", content_hash="b"
    )
    repository.set_story_order(db_conn, [doc_a, doc_b])

    repository.set_story_order(db_conn, [doc_b])

    story_documents = repository.list_story_documents(db_conn)
    assert [d["id"] for d in story_documents] == [doc_b]


def test_list_subplot_topics_orders_by_story_position_across_documents(db_conn):
    doc_later = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/book2.txt",
        filename="book2.txt",
        source_type="txt",
        content_hash="book2",
    )
    doc_earlier = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/book1.txt",
        filename="book1.txt",
        source_type="txt",
        content_hash="book1",
    )
    main_theme_id = repository.get_main_theme_id(db_conn)

    # doc_later was ingested first (lower id, would sort first by naive document_id
    # ordering) but belongs later in the story once explicitly ordered.
    seg_later = repository.insert_segment(db_conn, document_id=doc_later, sequence_index=0, text="Later text.")
    seg_earlier = repository.insert_segment(db_conn, document_id=doc_earlier, sequence_index=0, text="Earlier text.")

    topic_later = repository.insert_topic(
        db_conn,
        document_id=doc_later,
        theme_id=main_theme_id,
        sequence_index=0,
        title="Book 2 topic",
        summary="s",
        segment_start_id=seg_later,
        segment_end_id=seg_later,
    )
    topic_earlier = repository.insert_topic(
        db_conn,
        document_id=doc_earlier,
        theme_id=main_theme_id,
        sequence_index=0,
        title="Book 1 topic",
        summary="s",
        segment_start_id=seg_earlier,
        segment_end_id=seg_earlier,
    )

    subplot_id = repository.insert_subplot(db_conn, title="Cross-book subplot", summary="s")
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_later)
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_earlier)

    repository.set_story_order(db_conn, [doc_earlier, doc_later])

    ordered = repository.list_subplot_topics(db_conn, subplot_id)
    assert [t["id"] for t in ordered] == [topic_earlier, topic_later]


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
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=seg1,
        segment_end_id=seg2,
    )

    text = repository.get_topic_source_text(db_conn, topic_id)

    assert text == "First.\n\nSecond."
    assert "Third." not in text


def test_get_main_theme_id_is_a_singleton(db_conn):
    first = repository.get_main_theme_id(db_conn)
    second = repository.get_main_theme_id(db_conn)
    assert first == second

    main = next(t for t in repository.list_themes(db_conn) if t["id"] == first)
    assert main["is_main"] == 1


def test_retire_theme_moves_topics_to_main_and_deletes_subplot(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)
    subplot_id = repository.insert_subplot(
        db_conn, title="Ties to the Past", summary="A recurring thread.", theme_id=theme_id
    )

    repository.retire_theme(db_conn, theme_id)

    assert theme_id not in [t["id"] for t in repository.list_themes(db_conn)]
    assert subplot_id not in [s["id"] for s in repository.list_subplots(db_conn)]
    topic = repository.get_topics_by_ids(db_conn, [topic_ids[0]])[0]
    assert topic["theme_id"] == repository.get_main_theme_id(db_conn)


def test_retire_theme_is_a_no_op_for_main(db_conn):
    main_theme_id = repository.get_main_theme_id(db_conn)

    repository.retire_theme(db_conn, main_theme_id)

    assert repository.get_main_theme_id(db_conn) == main_theme_id

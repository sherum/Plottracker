from app.db import repository


def test_insert_and_list_documents(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="abc123",
    )

    documents = repository.list_documents(db_conn)

    assert len(documents) == 1
    assert documents[0]["id"] == doc_id
    assert documents[0]["role"] == "draft_script"
    assert documents[0]["source_type"] == "docx"


def test_get_document_returns_the_row(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="abc123",
    )

    document = repository.get_document(db_conn, doc_id)

    assert document["id"] == doc_id
    assert document["filename"] == "chapter1.docx"


def test_update_document_path_changes_filename_and_source_path(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="abc123",
    )

    updated = repository.update_document_path(
        db_conn, doc_id, filename="renamed.docx", source_path="draft_scripts/renamed.docx"
    )

    assert updated["filename"] == "renamed.docx"
    assert updated["source_path"] == "draft_scripts/renamed.docx"


def test_segments_ordered_by_sequence_index(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="xyz789",
    )

    repository.insert_segment(db_conn, document_id=doc_id, sequence_index=1, text="Second paragraph.")
    repository.insert_segment(db_conn, document_id=doc_id, sequence_index=0, text="First paragraph.")

    segments = repository.get_segments(db_conn, doc_id)

    assert [s["text"] for s in segments] == ["First paragraph.", "Second paragraph."]


def test_segment_styles_attached_to_segment(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="def456",
    )
    segment_id = repository.insert_segment(db_conn, document_id=doc_id, sequence_index=0, text="Bold text.")
    repository.insert_style(db_conn, segment_id=segment_id, style_kind="bold")
    repository.insert_style(db_conn, segment_id=segment_id, style_kind="highlight", style_value="yellow")

    segments = repository.get_segments(db_conn, doc_id)

    assert len(segments) == 1
    style_kinds = {s["style_kind"] for s in segments[0]["styles"]}
    assert style_kinds == {"bold", "highlight"}


def test_delete_document_removes_segments_topics_and_subplot_membership(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="ghi789",
    )
    segment_id = repository.insert_segment(db_conn, document_id=doc_id, sequence_index=0, text="Some text.")
    repository.insert_style(db_conn, segment_id=segment_id, style_kind="bold")

    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=doc_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=segment_id,
        segment_end_id=segment_id,
    )
    repository.set_topic_theme(db_conn, topic_id, theme_id)
    subplot_id = repository.insert_subplot(db_conn, title="A Subplot", summary="Summary.", theme_id=theme_id)
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_id)

    repository.delete_document(db_conn, doc_id)

    assert repository.list_documents(db_conn) == []
    assert repository.get_segments(db_conn, doc_id) == []
    assert repository.list_topics(db_conn, doc_id) == []
    assert repository.list_subplot_topics(db_conn, subplot_id) == []
    # The theme itself is not document-owned, so it survives with no topics.
    assert theme_id in [t["id"] for t in repository.list_themes(db_conn)]


def test_list_all_topics_resolves_chapter_title_and_page_number(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="chapter123",
    )
    heading_id = repository.insert_segment(
        db_conn, document_id=doc_id, sequence_index=0, text="Chapter One: The Beginning"
    )
    repository.insert_style(db_conn, segment_id=heading_id, style_kind="heading")
    body_id = repository.insert_segment(
        db_conn, document_id=doc_id, sequence_index=1, text="The story starts here.", page_number=3
    )
    repository.insert_topic(
        db_conn,
        document_id=doc_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="Opening scene",
        summary="Summary.",
        segment_start_id=body_id,
        segment_end_id=body_id,
    )

    topics = repository.list_all_topics(db_conn)

    assert topics[0]["chapter_title"] == "Chapter One: The Beginning"
    assert topics[0]["page_number"] == 3


def test_set_topic_act_updates_and_clears(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="act123",
    )
    segment_id = repository.insert_segment(db_conn, document_id=doc_id, sequence_index=0, text="Some text.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=doc_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=segment_id,
        segment_end_id=segment_id,
    )

    updated = repository.set_topic_act(db_conn, topic_id, "climax")
    assert updated["act"] == "climax"

    cleared = repository.set_topic_act(db_conn, topic_id, None)
    assert cleared["act"] is None


def test_update_encoding_rule_changes_fields(db_conn):
    rule_id = repository.insert_encoding_rule(
        db_conn,
        style_kind="italic",
        block_length="multi",
        position="chapter_start",
        label="dream_sequence",
        description="Original.",
    )

    updated = repository.update_encoding_rule(
        db_conn,
        rule_id,
        style_kind="bold",
        block_length="single",
        position="anywhere",
        label="renamed_rule",
        description="Revised.",
    )

    assert updated["style_kind"] == "bold"
    assert updated["block_length"] == "single"
    assert updated["position"] == "anywhere"
    assert updated["label"] == "renamed_rule"
    assert updated["description"] == "Revised."


def test_get_topic_segments_returns_ordered_rows_in_range(db_conn):
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
    repository.insert_segment(db_conn, document_id=document_id, sequence_index=2, text="Third.")
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

    segments = repository.get_topic_segments(db_conn, topic_id)

    assert [s["text"] for s in segments] == ["First.", "Second."]


def test_split_topic_divides_segments_and_shifts_sequence(db_conn):
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
    seg4 = repository.insert_segment(db_conn, document_id=document_id, sequence_index=3, text="Fourth.")
    seg5 = repository.insert_segment(db_conn, document_id=document_id, sequence_index=4, text="Fifth.")
    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        theme_id=theme_id,
        sequence_index=0,
        title="Original Topic",
        summary="Covers a lot of ground.",
        segment_start_id=seg1,
        segment_end_id=seg3,
        act="conflict",
    )
    next_topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        theme_id=theme_id,
        sequence_index=1,
        title="Next Topic",
        summary="Summary.",
        segment_start_id=seg4,
        segment_end_id=seg5,
    )

    result = repository.split_topic(db_conn, topic_id, seg2)

    assert result["original"]["segment_start_id"] == seg1
    assert result["original"]["segment_end_id"] == seg1
    assert result["original"]["sequence_index"] == 0

    assert result["new"]["segment_start_id"] == seg2
    assert result["new"]["segment_end_id"] == seg3
    assert result["new"]["sequence_index"] == 1
    assert result["new"]["theme_id"] == theme_id
    assert result["new"]["act"] == "conflict"
    assert result["new"]["title"] == "Original Topic"

    next_topic = repository.get_topics_by_ids(db_conn, [next_topic_id])[0]
    assert next_topic["sequence_index"] == 2


def test_unassign_topic_theme_moves_topic_to_main(db_conn):
    doc_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="draft_scripts/chapter1.docx",
        filename="chapter1.docx",
        source_type="docx",
        content_hash="unassign123",
    )
    segment_id = repository.insert_segment(db_conn, document_id=doc_id, sequence_index=0, text="Some text.")
    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=doc_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=segment_id,
        segment_end_id=segment_id,
    )
    repository.set_topic_theme(db_conn, topic_id, theme_id)

    main_theme_id = repository.get_main_theme_id(db_conn)
    updated = repository.unassign_topic_theme(db_conn, topic_id)

    assert updated["theme_id"] == main_theme_id
    assert repository.list_topics(db_conn, doc_id)[0]["theme_id"] == main_theme_id

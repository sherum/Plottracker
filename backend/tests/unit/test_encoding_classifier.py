from app.db import repository
from app.encoding.classifier import classify_document


def _make_document(db_conn) -> int:
    return repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/x.docx",
        filename="x.docx",
        source_type="docx",
        content_hash="hash",
    )


def _add_paragraph(db_conn, document_id, index, text, *, italic=False, heading=False):
    segment_id = repository.insert_segment(
        db_conn, document_id=document_id, sequence_index=index, paragraph_index=index, text=text
    )
    if italic:
        repository.insert_style(db_conn, segment_id=segment_id, style_kind="italic")
    if heading:
        repository.insert_style(db_conn, segment_id=segment_id, style_kind="heading")


def _semantic_tags_by_text(db_conn, document_id) -> dict[str, list[str]]:
    segments = repository.get_segments(db_conn, document_id)
    return {
        s["text"]: [st["style_value"] for st in s["styles"] if st["style_kind"] == "semantic"] for s in segments
    }


def _add_rules(db_conn):
    repository.insert_encoding_rule(
        db_conn, style_kind="italic", block_length="multi", position="chapter_start", label="dream_sequence"
    )
    repository.insert_encoding_rule(
        db_conn, style_kind="italic", block_length="single", position="anywhere", label="internal_dialogue"
    )


def test_multiline_italic_after_heading_is_dream_sequence(db_conn):
    document_id = _make_document(db_conn)
    _add_paragraph(db_conn, document_id, 0, "Chapter One", heading=True)
    _add_paragraph(db_conn, document_id, 1, "I was flying.", italic=True)
    _add_paragraph(db_conn, document_id, 2, "The ground fell away.", italic=True)
    _add_paragraph(db_conn, document_id, 3, "I woke up.")
    _add_rules(db_conn)

    summary = classify_document(db_conn, document_id)

    assert summary == {"tagged": 2}
    tags = _semantic_tags_by_text(db_conn, document_id)
    assert tags["I was flying."] == ["dream_sequence"]
    assert tags["The ground fell away."] == ["dream_sequence"]
    assert tags["I woke up."] == []


def test_single_italic_line_anywhere_is_internal_dialogue(db_conn):
    document_id = _make_document(db_conn)
    _add_paragraph(db_conn, document_id, 0, "He looked around.")
    _add_paragraph(db_conn, document_id, 1, "Where am I?", italic=True)
    _add_paragraph(db_conn, document_id, 2, "He kept walking.")
    _add_rules(db_conn)

    classify_document(db_conn, document_id)

    tags = _semantic_tags_by_text(db_conn, document_id)
    assert tags["Where am I?"] == ["internal_dialogue"]
    assert tags["He looked around."] == []


def test_multiline_italic_not_after_heading_is_untagged(db_conn):
    document_id = _make_document(db_conn)
    _add_paragraph(db_conn, document_id, 0, "He looked around.")
    _add_paragraph(db_conn, document_id, 1, "I was flying.", italic=True)
    _add_paragraph(db_conn, document_id, 2, "The ground fell away.", italic=True)
    _add_rules(db_conn)

    classify_document(db_conn, document_id)

    tags = _semantic_tags_by_text(db_conn, document_id)
    assert tags["I was flying."] == []
    assert tags["The ground fell away."] == []


def test_disabled_rule_does_not_tag_the_document(db_conn):
    document_id = _make_document(db_conn)
    _add_paragraph(db_conn, document_id, 0, "Chapter One", heading=True)
    _add_paragraph(db_conn, document_id, 1, "I was flying.", italic=True)
    _add_paragraph(db_conn, document_id, 2, "The ground fell away.", italic=True)
    _add_rules(db_conn)
    rule_id = repository.list_encoding_rules(db_conn)[0]["id"]
    repository.set_rule_enabled_for_document(db_conn, document_id, rule_id, False)

    summary = classify_document(db_conn, document_id)

    assert summary == {"tagged": 0}
    tags = _semantic_tags_by_text(db_conn, document_id)
    assert tags["I was flying."] == []
    assert tags["The ground fell away."] == []


def test_classify_is_idempotent(db_conn):
    document_id = _make_document(db_conn)
    _add_paragraph(db_conn, document_id, 0, "Where am I?", italic=True)
    _add_rules(db_conn)

    classify_document(db_conn, document_id)
    summary = classify_document(db_conn, document_id)

    assert summary == {"tagged": 1}
    segments = repository.get_segments(db_conn, document_id)
    semantic_tags = [st for s in segments for st in s["styles"] if st["style_kind"] == "semantic"]
    assert len(semantic_tags) == 1

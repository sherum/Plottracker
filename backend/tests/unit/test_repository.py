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

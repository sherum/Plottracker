from app.ingest.txt_extractor import TxtExtractor


def test_extracts_paragraphs_as_segments(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("First paragraph.\n\nSecond paragraph.\n\nThird paragraph.")

    result = TxtExtractor().extract(file_path)

    assert result.source_type == "txt"
    assert [s.text for s in result.segments] == [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph.",
    ]
    assert [s.sequence_index for s in result.segments] == [0, 1, 2]
    assert all(s.styles == [] for s in result.segments)


def test_md_suffix_reported_as_source_type(tmp_path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("Some notes.")

    result = TxtExtractor().extract(file_path)

    assert result.source_type == "md"

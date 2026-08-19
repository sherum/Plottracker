import pymupdf

from app.ingest.pdf_extractor import PdfExtractor


def _build_fixture(path):
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Bold text here.", fontname="hebo", fontsize=12)
    page.insert_text((72, 100), "Highlighted text here.", fontname="helv", fontsize=12)

    highlight_rect = pymupdf.Rect(65, 85, 220, 105)
    page.add_highlight_annot(highlight_rect)

    document.save(path)


def test_pdf_extractor_captures_page_number_and_bold(tmp_path):
    fixture_path = tmp_path / "sample.pdf"
    _build_fixture(fixture_path)

    result = PdfExtractor().extract(fixture_path)

    assert result.source_type == "pdf"
    assert result.page_count == 1
    assert all(s.page_number == 1 for s in result.segments)

    segments_by_text = {segment.text: segment for segment in result.segments}
    bold_styles = {s.style_kind for s in segments_by_text["Bold text here."].styles}
    assert "bold" in bold_styles


def test_pdf_extractor_captures_highlight_annotation(tmp_path):
    fixture_path = tmp_path / "sample.pdf"
    _build_fixture(fixture_path)

    result = PdfExtractor().extract(fixture_path)

    segments_by_text = {segment.text: segment for segment in result.segments}
    highlight_styles = {s.style_kind for s in segments_by_text["Highlighted text here."].styles}
    assert "highlight" in highlight_styles

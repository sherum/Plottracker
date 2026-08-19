from pathlib import Path

import pymupdf

from app.ingest.models import ExtractedDocument, ExtractedSegment, ExtractedStyle

BOLD_FLAG = 1 << 4
ITALIC_FLAG = 1 << 1


class PdfExtractor:
    def extract(self, path: Path) -> ExtractedDocument:
        document = pymupdf.open(path)
        segments: list[ExtractedSegment] = []
        sequence_index = 0

        for page_number, page in enumerate(document, start=1):
            annotations = list(page.annots())
            page_dict = page.get_text("dict")

            for block in page_dict["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        span_rect = pymupdf.Rect(span["bbox"])
                        styles = self._span_styles(span, span_rect, annotations)

                        segments.append(
                            ExtractedSegment(
                                sequence_index=sequence_index,
                                page_number=page_number,
                                text=text,
                                styles=styles,
                            )
                        )
                        sequence_index += 1

        return ExtractedDocument(source_type="pdf", page_count=document.page_count, segments=segments)

    @staticmethod
    def _span_styles(span: dict, span_rect: "pymupdf.Rect", annotations: list) -> list[ExtractedStyle]:
        styles: list[ExtractedStyle] = []
        flags = span["flags"]

        if flags & BOLD_FLAG:
            styles.append(ExtractedStyle(style_kind="bold"))
        if flags & ITALIC_FLAG:
            styles.append(ExtractedStyle(style_kind="italic"))

        for annot in annotations:
            if not annot.rect.intersects(span_rect):
                continue

            annot_type = annot.type[1]
            if annot_type == "Highlight":
                styles.append(ExtractedStyle(style_kind="highlight"))
            elif annot_type in ("Text", "FreeText"):
                content = (annot.info or {}).get("content")
                if content:
                    styles.append(ExtractedStyle(style_kind="comment", style_value=content))

        return styles

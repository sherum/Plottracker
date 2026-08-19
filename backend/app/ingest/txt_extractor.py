from pathlib import Path

from app.ingest.models import ExtractedDocument, ExtractedSegment


class TxtExtractor:
    def extract(self, path: Path) -> ExtractedDocument:
        text = path.read_text(encoding="utf-8")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        segments = [
            ExtractedSegment(sequence_index=i, paragraph_index=i, text=paragraph)
            for i, paragraph in enumerate(paragraphs)
        ]

        return ExtractedDocument(source_type=path.suffix.lstrip(".").lower(), segments=segments)

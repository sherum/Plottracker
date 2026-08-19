from pathlib import Path

from app.ingest.base import Extractor
from app.ingest.docx_extractor import DocxExtractor
from app.ingest.pdf_extractor import PdfExtractor
from app.ingest.txt_extractor import TxtExtractor

_EXTRACTORS: dict[str, Extractor] = {
    ".txt": TxtExtractor(),
    ".md": TxtExtractor(),
    ".docx": DocxExtractor(),
    ".pdf": PdfExtractor(),
}


def get_extractor(path: Path) -> Extractor | None:
    return _EXTRACTORS.get(path.suffix.lower())

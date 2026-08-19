from pathlib import Path
from typing import Protocol

from app.ingest.models import ExtractedDocument


class Extractor(Protocol):
    def extract(self, path: Path) -> ExtractedDocument: ...

import hashlib
import sqlite3
from pathlib import Path

from app.config import REPO_ROOT
from app.db import repository
from app.ingest.dispatcher import get_extractor


def ingest_folder(conn: sqlite3.Connection, folder_path: Path | str, role: str) -> dict:
    folder = Path(folder_path)
    if not folder.is_absolute():
        folder = REPO_ROOT / folder
    ingested: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []

    for file_path in sorted(folder.iterdir()):
        if not file_path.is_file():
            continue

        extractor = get_extractor(file_path)
        if extractor is None:
            skipped.append(file_path.name)
            continue

        try:
            _ingest_file(conn, file_path, extractor, role)
            ingested.append(file_path.name)
        except Exception as exc:
            failed.append({"filename": file_path.name, "error": str(exc)})

    return {"ingested": ingested, "skipped": skipped, "failed": failed}


def _ingest_file(conn: sqlite3.Connection, file_path: Path, extractor, role: str) -> None:
    extracted = extractor.extract(file_path)
    content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

    document_id = repository.insert_document(
        conn,
        role=role,
        source_path=str(file_path),
        filename=file_path.name,
        source_type=extracted.source_type,
        content_hash=content_hash,
        page_count=extracted.page_count,
    )

    for segment in extracted.segments:
        segment_id = repository.insert_segment(
            conn,
            document_id=document_id,
            sequence_index=segment.sequence_index,
            text=segment.text,
            page_number=segment.page_number,
            paragraph_index=segment.paragraph_index,
            char_start=segment.char_start,
            char_end=segment.char_end,
        )
        for style in segment.styles:
            repository.insert_style(
                conn,
                segment_id=segment_id,
                style_kind=style.style_kind,
                style_value=style.style_value,
            )

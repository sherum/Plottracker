import hashlib
import sqlite3
from pathlib import Path

from app.config import REPO_ROOT
from app.db import repository
from app.ingest.dispatcher import get_extractor

ROLE_DIRS = {"draft_script": "draft_scripts", "story_note": "story_notes"}


def ingest_folder(conn: sqlite3.Connection, folder_path: Path | str, role: str) -> dict:
    folder = Path(folder_path)
    if not folder.is_absolute():
        folder = REPO_ROOT / folder
    if not folder.is_dir():
        raise ValueError(f"folder not found: {folder}")

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


def upload_and_ingest(conn: sqlite3.Connection, *, filename: str, content: bytes, role: str) -> dict:
    if role not in ROLE_DIRS:
        raise ValueError(f"unknown role: {role}")
    if not filename:
        raise ValueError("missing filename")

    # Strip any path components the browser or client sent, so an upload can
    # only ever land inside its role's own folder.
    safe_name = Path(filename).name
    target_dir = REPO_ROOT / ROLE_DIRS[role]
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / safe_name

    extractor = get_extractor(file_path)
    if extractor is None:
        return {"ingested": [], "skipped": [safe_name], "failed": []}

    file_path.write_bytes(content)

    try:
        _ingest_file(conn, file_path, extractor, role)
        return {"ingested": [safe_name], "skipped": [], "failed": []}
    except Exception as exc:
        return {"ingested": [], "skipped": [], "failed": [{"filename": safe_name, "error": str(exc)}]}


def rename_document(conn: sqlite3.Connection, document_id: int, new_filename: str) -> dict:
    document = repository.get_document(conn, document_id)

    # Strip any path components the client sent, same as upload_and_ingest.
    safe_name = Path(new_filename).name
    old_path = Path(document["source_path"])
    new_path = old_path.parent / safe_name

    if new_path.exists():
        raise ValueError(f"a file named {safe_name!r} already exists")

    old_path.rename(new_path)

    return repository.update_document_path(conn, document_id, filename=safe_name, source_path=str(new_path))


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

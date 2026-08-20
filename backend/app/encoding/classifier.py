import sqlite3
from itertools import groupby
from typing import TypedDict

from app.db import repository


class Block(TypedDict):
    segments: list[dict]
    paragraph_count: int
    preceded_by_heading: bool


def classify_document(conn: sqlite3.Connection, document_id: int) -> dict:
    segments = repository.get_segments(conn, document_id)
    rules = repository.list_encoding_rules(conn)
    if not rules:
        return {"tagged": 0}

    repository.clear_semantic_styles_for_document(conn, document_id)

    rules_by_style_kind: dict[str, list[dict]] = {}
    for rule in rules:
        rules_by_style_kind.setdefault(rule["style_kind"], []).append(rule)

    paragraphs = _group_by_paragraph(segments)

    tagged = 0
    for style_kind, style_rules in rules_by_style_kind.items():
        for block in _find_blocks(paragraphs, style_kind):
            block_length = "single" if block["paragraph_count"] == 1 else "multi"
            position = "chapter_start" if block["preceded_by_heading"] else "anywhere"
            for rule in style_rules:
                if rule["block_length"] != block_length or rule["position"] != position:
                    continue
                for segment in block["segments"]:
                    repository.insert_style(
                        conn, segment_id=segment["id"], style_kind="semantic", style_value=rule["label"]
                    )
                    tagged += 1

    return {"tagged": tagged}


def _group_by_paragraph(segments: list[dict]) -> list[dict]:
    """Group segments (runs) by paragraph. Blank paragraphs have no runs and
    so never appear here — consecutive entries in this list are therefore
    already "adjacent content", regardless of how many blank Word paragraphs
    separate them in the source document."""
    paragraphs = []
    for _, group in groupby(segments, key=lambda s: s["paragraph_index"]):
        para_segments = list(group)
        paragraphs.append(
            {
                "segments": para_segments,
                "is_heading": any(any(st["style_kind"] == "heading" for st in seg["styles"]) for seg in para_segments),
            }
        )
    return paragraphs


def _find_blocks(paragraphs: list[dict], style_kind: str) -> list[Block]:
    blocks: list[Block] = []
    current_segments: list[dict] = []
    current_paragraph_count = 0
    current_preceded_by_heading = False
    pending_heading = False

    def flush() -> None:
        nonlocal current_segments, current_paragraph_count, current_preceded_by_heading
        if current_segments:
            blocks.append(
                {
                    "segments": current_segments,
                    "paragraph_count": current_paragraph_count,
                    "preceded_by_heading": current_preceded_by_heading,
                }
            )
        current_segments = []
        current_paragraph_count = 0
        current_preceded_by_heading = False

    for paragraph in paragraphs:
        if paragraph["is_heading"]:
            flush()
            pending_heading = True
            continue

        is_styled = all(any(st["style_kind"] == style_kind for st in seg["styles"]) for seg in paragraph["segments"])
        if is_styled:
            if not current_segments:
                current_preceded_by_heading = pending_heading
            current_segments.extend(paragraph["segments"])
            current_paragraph_count += 1
        else:
            flush()
        pending_heading = False

    flush()
    return blocks

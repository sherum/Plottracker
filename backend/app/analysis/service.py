import sqlite3

from app.analysis import llm
from app.analysis.models import AnalysisResult, TopicOut
from app.db import repository


def _is_heading(segment: dict) -> bool:
    return any(style["style_kind"] == "heading" for style in segment["styles"])


def _trim_trailing_chapter_headings(result: AnalysisResult, segments: list[dict]) -> AnalysisResult:
    """A topic's segment_end_id must never be the next chapter's heading line."""
    position_by_id = {s["id"]: i for i, s in enumerate(segments)}

    def trim(topic: TopicOut) -> TopicOut:
        if topic.segment_end_id == topic.segment_start_id:
            return topic
        end_segment = segments[position_by_id[topic.segment_end_id]]
        if not _is_heading(end_segment):
            return topic
        end_position = position_by_id[topic.segment_end_id]
        if end_position == 0:
            return topic
        return topic.model_copy(update={"segment_end_id": segments[end_position - 1]["id"]})

    return result.model_copy(update={"topics": [trim(topic) for topic in result.topics]})


def analyze_document(conn: sqlite3.Connection, document_id: int) -> dict:
    segments = repository.get_segments(conn, document_id)
    if not segments:
        raise ValueError(f"document {document_id} has no segments")

    result = llm.extract_topics_and_themes(segments)
    result = _trim_trailing_chapter_headings(result, segments)

    repository.exclude_topics_for_document(conn, document_id)

    topic_ids = [
        repository.insert_topic(
            conn,
            document_id=document_id,
            sequence_index=index,
            title=topic.title,
            summary=topic.summary,
            segment_start_id=topic.segment_start_id,
            segment_end_id=topic.segment_end_id,
            act=topic.act,
        )
        for index, topic in enumerate(result.topics)
    ]

    theme_ids = []
    for theme in result.themes:
        theme_id = repository.insert_theme(conn, title=theme.title, summary=theme.summary)
        theme_ids.append(theme_id)
        for topic_index in theme.topic_indices:
            repository.set_topic_theme(conn, topic_ids[topic_index], theme_id)

    return {"topics_created": len(topic_ids), "themes_created": len(theme_ids)}

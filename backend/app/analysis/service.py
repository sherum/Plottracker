import sqlite3

from app.analysis import llm
from app.db import repository


def analyze_document(conn: sqlite3.Connection, document_id: int) -> dict:
    segments = repository.get_segments(conn, document_id)
    if not segments:
        raise ValueError(f"document {document_id} has no segments")

    result = llm.extract_topics_and_themes(segments)

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

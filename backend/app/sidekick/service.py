import sqlite3

from app.db import repository
from app.sidekick import llm


def ask(
    conn: sqlite3.Connection,
    question: str,
    topic_ids: list[int],
    current_topic_id: int | None = None,
    current_theme_id: int | None = None,
) -> tuple[str, list[str], int | None]:
    topics = repository.get_topics_by_ids(conn, topic_ids)
    theme_ids = sorted({t["theme_id"] for t in topics if t["theme_id"] is not None})
    themes = repository.get_themes_by_ids(conn, theme_ids)
    encoding_rules = repository.list_encoding_rules(conn)
    document_ids = {t["document_id"] for t in topics}
    document_id = document_ids.pop() if len(document_ids) == 1 else None
    subplots = repository.list_subplots(conn, document_id)
    return llm.answer_question(
        conn,
        question,
        topics,
        themes,
        encoding_rules,
        subplots,
        current_topic_id=current_topic_id,
        current_theme_id=current_theme_id,
    )

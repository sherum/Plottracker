import sqlite3

from app.db import repository
from app.sidekick import llm


def ask(conn: sqlite3.Connection, question: str, topic_ids: list[int]) -> str:
    topics = repository.get_topics_by_ids(conn, topic_ids)
    theme_ids = sorted({t["theme_id"] for t in topics if t["theme_id"] is not None})
    themes = repository.get_themes_by_ids(conn, theme_ids)
    return llm.answer_question(question, topics, themes)

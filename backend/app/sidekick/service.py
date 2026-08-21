import sqlite3

from app.db import repository
from app.sidekick import llm


def ask(conn: sqlite3.Connection, question: str, topic_ids: list[int]) -> tuple[str, list[str]]:
    topics = repository.get_topics_by_ids(conn, topic_ids)
    theme_ids = sorted({t["theme_id"] for t in topics if t["theme_id"] is not None})
    themes = repository.get_themes_by_ids(conn, theme_ids)
    encoding_rules = repository.list_encoding_rules(conn)
    return llm.answer_question(conn, question, topics, themes, encoding_rules)

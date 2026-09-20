import sqlite3

from app.db import repository
from app.sidekick import llm


def ask(
    conn: sqlite3.Connection,
    question: str,
    topic_ids: list[int],
    current_topic_id: int | None = None,
    current_theme_id: int | None = None,
    add_target_subplot_id: int | None = None,
    add_target_is_new: bool = False,
    story_id: int | None = None,
) -> tuple[str, list[str], int | None, list[int] | None]:
    topics = repository.get_topics_by_ids(conn, topic_ids)
    # Themes aren't scoped to a document, and a brand-new theme has no topics
    # yet, so derive the theme list from the theme table itself, not from the
    # topics currently in scope - otherwise an empty theme would be invisible.
    themes = [t for t in repository.list_themes(conn, story_id) if not t["excluded"]]
    encoding_rules = repository.list_encoding_rules(conn)
    document_ids = {t["document_id"] for t in topics}
    document_id = document_ids.pop() if len(document_ids) == 1 else None
    subplots = repository.list_subplots(conn, document_id, story_id)
    for subplot in subplots:
        subplot["topic_ids"] = repository.list_subplot_topic_ids(conn, subplot["id"])
    return llm.answer_question(
        conn,
        question,
        topics,
        themes,
        encoding_rules,
        subplots,
        current_topic_id=current_topic_id,
        current_theme_id=current_theme_id,
        add_target_subplot_id=add_target_subplot_id,
        add_target_is_new=add_target_is_new,
        story_id=story_id,
    )

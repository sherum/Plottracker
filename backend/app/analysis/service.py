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


MAX_AUTO_SUBPLOTS = 4


def analyze_document(conn: sqlite3.Connection, document_id: int) -> dict:
    segments = repository.get_segments(conn, document_id)
    if not segments:
        raise ValueError(f"document {document_id} has no segments")

    existing_themes = repository.list_active_themes(conn)
    result = llm.extract_topics_and_themes(segments, existing_themes)
    result = _trim_trailing_chapter_headings(result, segments)

    main_theme_id = repository.get_main_theme_id(conn)
    existing_theme_ids = {theme["id"] for theme in existing_themes}

    # A reanalyze pass excludes this document's old topics; themes/subplots
    # are left alone even if that empties one out. They may be manually
    # curated, and a later pass may repopulate them - only the user retires
    # a theme, via exclude_theme.
    repository.exclude_topics_for_document(conn, document_id)

    # Every topic starts under Main; only topics grouped into one of the
    # top MAX_AUTO_SUBPLOTS themes (by topic count) get moved into a subplot.
    topic_ids = [
        repository.insert_topic(
            conn,
            document_id=document_id,
            theme_id=main_theme_id,
            sequence_index=index,
            title=topic.title,
            summary=topic.summary,
            segment_start_id=topic.segment_start_id,
            segment_end_id=topic.segment_end_id,
            act=topic.act,
        )
        for index, topic in enumerate(result.topics)
    ]

    valid_indices = range(len(topic_ids))
    themes_with_indices = [
        (theme, [i for i in theme.topic_indices if i in valid_indices])
        for theme in result.themes
    ]

    # A theme continuing an existing one is reused directly, with no cap -
    # it's not a new subplot. Only genuinely new clusters compete for the
    # MAX_AUTO_SUBPLOTS budget, largest first.
    reused = [
        (theme, indices)
        for theme, indices in themes_with_indices
        if indices and theme.existing_theme_id in existing_theme_ids
    ]
    new = sorted(
        (
            (theme, indices)
            for theme, indices in themes_with_indices
            if indices and theme.existing_theme_id not in existing_theme_ids
        ),
        key=lambda pair: len(pair[1]),
        reverse=True,
    )

    theme_ids = []
    for theme, indices in reused:
        theme_id = theme.existing_theme_id
        for topic_index in indices:
            repository.set_topic_theme(conn, topic_ids[topic_index], theme_id)

    for theme, indices in new[:MAX_AUTO_SUBPLOTS]:
        theme_id = repository.insert_theme(conn, title=theme.title, summary=theme.summary)
        repository.insert_subplot(conn, title=theme.title, summary=theme.summary, theme_id=theme_id)
        theme_ids.append(theme_id)
        for topic_index in indices:
            repository.set_topic_theme(conn, topic_ids[topic_index], theme_id)

    return {"topics_created": len(topic_ids), "themes_created": len(theme_ids)}

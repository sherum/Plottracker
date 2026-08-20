from app.db import repository


def _make_document_with_topics(db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Text.")
    theme_id = repository.insert_theme(db_conn, title="Ties to the Past", summary="A recurring thread.")
    topic_ids = [
        repository.insert_topic(
            db_conn,
            document_id=document_id,
            sequence_index=i,
            title=title,
            summary=title,
            segment_start_id=segment_id,
            segment_end_id=segment_id,
            act="opening",
        )
        for i, title in enumerate(["First topic", "Second topic"])
    ]
    repository.set_topic_theme(db_conn, topic_ids[0], theme_id)
    return document_id, theme_id, topic_ids


def test_promote_theme_to_subplot_copies_its_topics(db_conn):
    _, theme_id, topic_ids = _make_document_with_topics(db_conn)

    subplot_id = repository.promote_theme_to_subplot(db_conn, theme_id)

    subplot = repository.get_subplot(db_conn, subplot_id)
    assert subplot["theme_id"] == theme_id
    assert subplot["title"] == "Ties to the Past"
    assert subplot["topic_count"] == 1

    subplot_topics = repository.list_subplot_topics(db_conn, subplot_id)
    assert [t["id"] for t in subplot_topics] == [topic_ids[0]]


def test_manual_subplot_add_and_remove_topic(db_conn):
    _, _, topic_ids = _make_document_with_topics(db_conn)

    subplot_id = repository.insert_subplot(db_conn, title="Author's Subplot", summary="Manually created.")
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 0

    repository.add_topic_to_subplot(db_conn, subplot_id, topic_ids[1])
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 1

    repository.remove_topic_from_subplot(db_conn, subplot_id, topic_ids[1])
    assert repository.get_subplot(db_conn, subplot_id)["topic_count"] == 0

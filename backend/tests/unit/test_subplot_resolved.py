from app.db import repository
from app.db.stories import assign_story


def _edition(db_conn, filename):
    document_id = repository.insert_document(
        db_conn, role="draft_script", source_path=f"/tmp/{filename}", filename=filename, source_type="txt",
        content_hash=filename,
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="A scene.")
    assign_story(db_conn, document_id)
    return document_id, segment_id


def _add_topic(db_conn, document_id, segment_id, subplot_id):
    theme_id = repository.get_subplot(db_conn, subplot_id)["theme_id"]
    return repository.insert_topic(
        db_conn, document_id=document_id, theme_id=theme_id, sequence_index=0, title="t", summary="s",
        segment_start_id=segment_id, segment_end_id=segment_id,
    )


def _subplot(db_conn, document_id):
    story_id = repository.get_document(db_conn, document_id)["story_id"]
    return repository.insert_subplot(db_conn, title="Rebellion", summary="s", story_id=story_id)


def test_new_subplots_are_open(db_conn):
    doc, _ = _edition(db_conn, "saga_1.txt")

    subplot = repository.get_subplot(db_conn, _subplot(db_conn, doc))

    assert subplot["resolved"] is False
    assert subplot["reopened_after_resolution"] is False


def test_marking_resolved_records_the_last_edition_it_appears_in(db_conn):
    edition_1, segment_1 = _edition(db_conn, "saga_1.txt")
    edition_2, segment_2 = _edition(db_conn, "saga_2.txt")
    subplot_id = _subplot(db_conn, edition_1)
    _add_topic(db_conn, edition_1, segment_1, subplot_id)
    _add_topic(db_conn, edition_2, segment_2, subplot_id)

    subplot = repository.set_subplot_resolved(db_conn, subplot_id, True)

    assert subplot["resolved"] is True
    assert (subplot["first_position"], subplot["last_position"], subplot["resolved_at_position"]) == (1, 2, 2)
    assert subplot["reopened_after_resolution"] is False


def test_a_resolved_subplot_that_reappears_in_a_later_edition_is_flagged(db_conn):
    edition_1, segment_1 = _edition(db_conn, "saga_1.txt")
    edition_2, segment_2 = _edition(db_conn, "saga_2.txt")
    subplot_id = _subplot(db_conn, edition_1)
    _add_topic(db_conn, edition_1, segment_1, subplot_id)
    repository.set_subplot_resolved(db_conn, subplot_id, True)

    _add_topic(db_conn, edition_2, segment_2, subplot_id)

    assert repository.get_subplot(db_conn, subplot_id)["reopened_after_resolution"] is True


def test_reopening_clears_the_resolution(db_conn):
    doc, segment = _edition(db_conn, "saga_1.txt")
    subplot_id = _subplot(db_conn, doc)
    _add_topic(db_conn, doc, segment, subplot_id)
    repository.set_subplot_resolved(db_conn, subplot_id, True)

    subplot = repository.set_subplot_resolved(db_conn, subplot_id, False)

    assert subplot["resolved"] is False
    assert subplot["resolved_at_position"] is None


def test_patch_endpoint_and_listing_expose_the_state(client, db_conn):
    doc, _ = _edition(db_conn, "saga_1.txt")
    subplot_id = _subplot(db_conn, doc)

    response = client.patch(f"/subplots/{subplot_id}", json={"resolved": True})

    assert response.status_code == 200
    assert response.json()["resolved"] is True
    assert [s["resolved"] for s in client.get("/subplots").json()] == [True]


def test_sidekick_can_mark_a_subplot_resolved_and_sees_the_state(db_conn):
    from app.sidekick.llm import _build_context
    from app.sidekick.tools import execute_tool

    doc, _ = _edition(db_conn, "saga_1.txt")
    subplot_id = _subplot(db_conn, doc)

    result = execute_tool(db_conn, "set_subplot_resolved", {"subplot_id": subplot_id, "resolved": True})

    assert result["resolved"] is True
    context = _build_context([], [], [], repository.list_subplots(db_conn), None, None)
    assert "resolved): Rebellion" in context

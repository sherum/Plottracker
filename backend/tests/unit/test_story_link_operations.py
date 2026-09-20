import pytest

from app.db import repository
from app.db.stories import assign_story
from app.db.story_links import link_stories, unlink_story


def _edition(db_conn, filename):
    document_id = repository.insert_document(
        db_conn, role="draft_script", source_path=f"/tmp/{filename}", filename=filename, source_type="docx",
        content_hash=filename,
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="A scene.")
    assign_story(db_conn, document_id)
    return document_id, segment_id


def _story_id(db_conn, document_id):
    return repository.get_document(db_conn, document_id)["story_id"]


def _topic(db_conn, document_id, segment_id, theme_id):
    return repository.insert_topic(
        db_conn, document_id=document_id, theme_id=theme_id, sequence_index=0, title="t", summary="s",
        segment_start_id=segment_id, segment_end_id=segment_id,
    )


def _order(db_conn, story_id):
    return [d["filename"] for d in repository.list_story_documents(db_conn, story_id)]


def _mains(db_conn):
    return db_conn.execute("SELECT COUNT(*) FROM themes WHERE is_main = 1 AND story_id IS NOT NULL").fetchone()[0]


def _theme_of(db_conn, subplot_id):
    return repository.get_subplot(db_conn, subplot_id)["theme_id"]


def test_linking_puts_the_second_story_after_the_first_under_one_main(db_conn):
    a1, seg_a1 = _edition(db_conn, "alpha_1.docx")
    _edition(db_conn, "alpha_2.docx")
    b1, seg_b1 = _edition(db_conn, "beta.docx")
    story_a, story_b = _story_id(db_conn, a1), _story_id(db_conn, b1)
    main_a, main_b = repository.get_main_theme_id(db_conn, story_a), repository.get_main_theme_id(db_conn, story_b)
    topic_a, topic_b = _topic(db_conn, a1, seg_a1, main_a), _topic(db_conn, b1, seg_b1, main_b)

    survivor = link_stories(db_conn, story_a, story_b)

    assert survivor == story_a
    assert _order(db_conn, story_a) == ["alpha_1.docx", "alpha_2.docx", "beta.docx"]
    assert _story_id(db_conn, b1) == story_a
    assert db_conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0] == 1
    assert _mains(db_conn) == 1
    assert repository.get_topics_by_ids(db_conn, [topic_a, topic_b])[0]["theme_id"] == main_a
    assert repository.get_topics_by_ids(db_conn, [topic_b])[0]["theme_id"] == main_a


def test_flip_puts_the_other_story_first(db_conn):
    a1, _ = _edition(db_conn, "alpha.docx")
    b1, _ = _edition(db_conn, "beta.docx")

    survivor = link_stories(db_conn, _story_id(db_conn, b1), _story_id(db_conn, a1))

    assert _order(db_conn, survivor) == ["beta.docx", "alpha.docx"]


def test_a_story_cannot_be_linked_to_itself(db_conn):
    a1, _ = _edition(db_conn, "alpha.docx")
    story = _story_id(db_conn, a1)

    with pytest.raises(ValueError):
        link_stories(db_conn, story, story)


def test_linking_carries_subplots_and_shifts_their_resolution_position(db_conn):
    a1, _ = _edition(db_conn, "alpha_1.docx")
    _edition(db_conn, "alpha_2.docx")
    b1, seg_b1 = _edition(db_conn, "beta.docx")
    story_a, story_b = _story_id(db_conn, a1), _story_id(db_conn, b1)
    subplot = repository.insert_subplot(db_conn, title="Beta plot", summary="s", story_id=story_b)
    _topic(db_conn, b1, seg_b1, _theme_of(db_conn, subplot))
    repository.set_subplot_resolved(db_conn, subplot, True)  # resolved at position 1 of beta's own story

    link_stories(db_conn, story_a, story_b)

    carried = repository.get_subplot(db_conn, subplot)
    assert repository.get_theme(db_conn, carried["theme_id"])["story_id"] == story_a
    assert (carried["first_position"], carried["resolved_at_position"]) == (3, 3)
    assert carried["reopened_after_resolution"] is False


def test_a_trilogy_is_linked_one_book_at_a_time(db_conn):
    docs = {name: _edition(db_conn, f"{name}.docx")[0] for name in ("book_one", "book_two", "book_three")}
    story = link_stories(db_conn, _story_id(db_conn, docs["book_one"]), _story_id(db_conn, docs["book_two"]))

    story = link_stories(db_conn, story, _story_id(db_conn, docs["book_three"]))

    assert _order(db_conn, story) == ["book_one.docx", "book_two.docx", "book_three.docx"]
    assert _mains(db_conn) == 1


def test_a_later_upload_joins_the_linked_story_by_either_name(db_conn):
    a1, _ = _edition(db_conn, "alpha.docx")
    b1, _ = _edition(db_conn, "beta.docx")
    story = link_stories(db_conn, _story_id(db_conn, a1), _story_id(db_conn, b1))

    b2, _ = _edition(db_conn, "beta_2.docx")

    assert _story_id(db_conn, b2) == story
    assert _order(db_conn, story) == ["alpha.docx", "beta.docx", "beta_2.docx"]


def test_unlinking_detaches_the_last_story_and_splits_the_plot(db_conn):
    a1, seg_a1 = _edition(db_conn, "alpha.docx")
    b1, seg_b1 = _edition(db_conn, "beta.docx")
    story_a, story_b = _story_id(db_conn, a1), _story_id(db_conn, b1)
    main_a = repository.get_main_theme_id(db_conn, story_a)
    beta_only = repository.insert_subplot(db_conn, title="Beta only", summary="s", story_id=story_b)
    spanning = repository.insert_subplot(db_conn, title="Spans both", summary="s", story_id=story_a)
    beta_theme, span_theme = _theme_of(db_conn, beta_only), _theme_of(db_conn, spanning)
    main_topic = _topic(db_conn, b1, seg_b1, repository.get_main_theme_id(db_conn, story_b))
    beta_topic = _topic(db_conn, b1, seg_b1, beta_theme)
    span_in_alpha = _topic(db_conn, a1, seg_a1, span_theme)
    span_in_beta = _topic(db_conn, b1, seg_b1, span_theme)
    linked = link_stories(db_conn, story_a, story_b)

    detached = unlink_story(db_conn, linked)

    assert _story_id(db_conn, b1) == detached != linked
    assert _order(db_conn, linked) == ["alpha.docx"]
    assert _order(db_conn, detached) == ["beta.docx"]
    assert _mains(db_conn) == 2
    new_main = repository.get_main_theme_id(db_conn, detached)
    topics = {
        t["id"]: t["theme_id"]
        for t in repository.get_topics_by_ids(db_conn, [main_topic, beta_topic, span_in_alpha, span_in_beta])
    }
    assert topics[main_topic] == new_main  # Main topics follow their document
    assert topics[beta_topic] == beta_theme  # a subplot living only in beta goes with it
    assert repository.get_theme(db_conn, beta_theme)["story_id"] == detached
    assert topics[span_in_alpha] == span_theme  # a spanning subplot stays with the earlier story
    assert topics[span_in_beta] == new_main  # ...and its topic in the detached book leaves it
    assert repository.get_theme(db_conn, span_theme)["story_id"] == linked
    assert repository.get_main_theme_id(db_conn, linked) == main_a


def test_a_story_with_one_name_cannot_be_unlinked(db_conn):
    a1, _ = _edition(db_conn, "alpha.docx")

    with pytest.raises(ValueError):
        unlink_story(db_conn, _story_id(db_conn, a1))

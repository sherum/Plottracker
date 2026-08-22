from app.db import repository
from app.sidekick.tools import execute_tool


def _make_topic_and_theme(db_conn):
    document_id = repository.insert_document(
        db_conn,
        role="draft_script",
        source_path="/tmp/chapter1.txt",
        filename="chapter1.txt",
        source_type="txt",
        content_hash="hash",
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="Text.")
    theme_id = repository.insert_theme(db_conn, title="A Theme", summary="Summary.")
    topic_id = repository.insert_topic(
        db_conn,
        document_id=document_id,
        theme_id=repository.get_main_theme_id(db_conn),
        sequence_index=0,
        title="A Topic",
        summary="Summary.",
        segment_start_id=segment_id,
        segment_end_id=segment_id,
    )
    repository.set_topic_theme(db_conn, topic_id, theme_id)
    return topic_id, theme_id


def test_set_topic_excluded_tool(db_conn):
    topic_id, _ = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "set_topic_excluded", {"topic_id": topic_id, "excluded": True})

    assert result["excluded"] == 1
    assert repository.list_topics(db_conn, repository.list_documents(db_conn)[0]["id"])[0]["excluded"] == 1


def test_set_theme_excluded_tool(db_conn):
    _, theme_id = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "set_theme_excluded", {"theme_id": theme_id, "excluded": True})

    assert result["excluded"] == 1


def test_add_then_remove_topic_from_subplot_tools(db_conn):
    topic_id, theme_id = _make_topic_and_theme(db_conn)
    subplot_id = repository.insert_subplot(db_conn, title="A Subplot", summary="Summary.", theme_id=theme_id)

    added = execute_tool(db_conn, "add_topic_to_subplot", {"subplot_id": subplot_id, "topic_id": topic_id})
    assert added["topic_count"] == 1

    removed = execute_tool(db_conn, "remove_topic_from_subplot", {"subplot_id": subplot_id, "topic_id": topic_id})
    assert removed["topic_count"] == 0


def test_create_subplot_tool(db_conn):
    result = execute_tool(db_conn, "create_subplot", {"title": "New Subplot", "summary": "Fresh start."})

    assert result["title"] == "New Subplot"
    assert result["summary"] == "Fresh start."
    assert result["topic_count"] == 0
    assert any(t["title"] == "New Subplot" for t in repository.list_themes(db_conn))


def test_assign_topic_to_theme_tool_moves_topic(db_conn):
    topic_id, old_theme_id = _make_topic_and_theme(db_conn)
    new_theme_id = repository.insert_theme(db_conn, title="Another Theme", summary="Summary.")

    result = execute_tool(db_conn, "assign_topic_to_theme", {"topic_id": topic_id, "theme_id": new_theme_id})

    assert result["theme_id"] == new_theme_id
    assert result["theme_id"] != old_theme_id


def test_delete_subplot_tool(db_conn):
    topic_id, theme_id = _make_topic_and_theme(db_conn)
    subplot_id = repository.insert_subplot(db_conn, title="A Subplot", summary="Summary.", theme_id=theme_id)
    repository.add_topic_to_subplot(db_conn, subplot_id, topic_id)

    result = execute_tool(db_conn, "delete_subplot", {"subplot_id": subplot_id})

    assert result == {"deleted": subplot_id}
    assert subplot_id not in [s["id"] for s in repository.list_subplots(db_conn)]


def test_filter_topics_tool_returns_matching_topics(db_conn):
    topic_id, _ = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "filter_topics", {"topic_ids": [topic_id]})

    assert [t["id"] for t in result] == [topic_id]


def test_set_main_theme_tool(db_conn):
    _, theme_id = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "set_main_theme", {"theme_id": theme_id})

    assert result["id"] == theme_id
    assert result["is_main"] == 1
    assert repository.get_main_theme_id(db_conn) == theme_id


def test_remove_topic_from_theme_tool(db_conn):
    topic_id, theme_id = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "remove_topic_from_theme", {"topic_id": topic_id})

    assert result["theme_id"] == repository.get_main_theme_id(db_conn)
    assert result["theme_id"] != theme_id


def test_set_topic_act_tool_and_unassigned_sentinel(db_conn):
    topic_id, _ = _make_topic_and_theme(db_conn)

    result = execute_tool(db_conn, "set_topic_act", {"topic_id": topic_id, "act": "climax"})
    assert result["act"] == "climax"

    cleared = execute_tool(db_conn, "set_topic_act", {"topic_id": topic_id, "act": "unassigned"})
    assert cleared["act"] is None


def test_add_update_delete_encoding_rule_tools(db_conn):
    added = execute_tool(
        db_conn,
        "add_encoding_rule",
        {
            "style_kind": "italic",
            "block_length": "multi",
            "position": "chapter_start",
            "label": "dream_sequence",
            "description": "Original.",
        },
    )
    rule_id = added["id"]
    assert repository.list_encoding_rules(db_conn)[0]["label"] == "dream_sequence"

    updated = execute_tool(
        db_conn,
        "update_encoding_rule",
        {
            "rule_id": rule_id,
            "style_kind": "bold",
            "block_length": "single",
            "position": "anywhere",
            "label": "renamed",
            "description": "Revised.",
        },
    )
    assert updated["label"] == "renamed"

    deleted = execute_tool(db_conn, "delete_encoding_rule", {"rule_id": rule_id})
    assert deleted == {"deleted": rule_id}
    assert repository.list_encoding_rules(db_conn) == []


def test_execute_tool_unknown_name_returns_error(db_conn):
    result = execute_tool(db_conn, "delete_everything", {})
    assert "error" in result


def test_execute_tool_nonexistent_id_returns_error_not_raise(db_conn):
    result = execute_tool(db_conn, "set_topic_excluded", {"topic_id": 999999, "excluded": True})
    assert "error" in result

from app.db import repository
from app.sidekick import llm, service


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
    main_theme_id = repository.get_main_theme_id(db_conn)
    topic_ids = [
        repository.insert_topic(
            db_conn,
            document_id=document_id,
            theme_id=main_theme_id,
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
    return theme_id, topic_ids


def test_ask_includes_empty_theme_with_no_topics_yet(db_conn, monkeypatch):
    _, topic_ids = _make_document_with_topics(db_conn)
    empty_theme_id = repository.insert_theme(db_conn, title="Brand New Theme", summary="No topics yet.")

    captured = {}
    monkeypatch.setattr(
        llm,
        "answer_question",
        lambda conn, question, topics, themes, encoding_rules, subplots, **kwargs: (
            captured.update(themes=themes) or "answer",
            [],
            None,
            None,
        ),
    )

    service.ask(db_conn, "What themes exist?", [topic_ids[0]])

    assert empty_theme_id in [t["id"] for t in captured["themes"]]


def test_ask_scopes_context_to_given_topic_ids(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)

    captured = {}

    def fake_answer_question(
        conn, question, topics, themes, encoding_rules, subplots, current_topic_id=None, current_theme_id=None, **kwargs
    ):
        captured["question"] = question
        captured["topics"] = topics
        captured["themes"] = themes
        captured["current_topic_id"] = current_topic_id
        captured["current_theme_id"] = current_theme_id
        return "The answer.", [], None, None

    monkeypatch.setattr(llm, "answer_question", fake_answer_question)

    answer, actions, created_subplot_id, filtered_topic_ids = service.ask(
        db_conn, "What happens first?", [topic_ids[0]], current_topic_id=topic_ids[0], current_theme_id=theme_id
    )

    assert answer == "The answer."
    assert actions == []
    assert created_subplot_id is None
    assert filtered_topic_ids is None
    assert captured["question"] == "What happens first?"
    assert [t["title"] for t in captured["topics"]] == ["First topic"]
    # All non-excluded themes are in scope, including Main - not just the
    # one the given topic happens to belong to.
    assert theme_id in [t["id"] for t in captured["themes"]]
    assert repository.get_main_theme_id(db_conn) in [t["id"] for t in captured["themes"]]
    assert captured["current_topic_id"] == topic_ids[0]
    assert captured["current_theme_id"] == theme_id


def test_ask_omits_excluded_topics_even_when_explicitly_requested(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)
    repository.set_topic_excluded(db_conn, topic_ids[0], True)

    captured = {}
    monkeypatch.setattr(
        llm,
        "answer_question",
        lambda conn, question, topics, themes, encoding_rules, subplots, **kwargs: (
            captured.update(topics=topics) or "answer",
            [],
            None,
            None,
        ),
    )

    service.ask(db_conn, "What happens first?", [topic_ids[0], topic_ids[1]])

    assert [t["id"] for t in captured["topics"]] == [topic_ids[1]]


class _FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, call_id, name, arguments):
        self.id = call_id
        self.function = _FakeFunction(name, arguments)


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _FakeResponse:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})]


def test_answer_question_executes_tool_call_then_returns_final_answer(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)
    topic_id = topic_ids[0]

    responses = [
        _FakeResponse(
            _FakeMessage(
                tool_calls=[
                    _FakeToolCall(
                        "call_1",
                        "set_topic_excluded",
                        f'{{"topic_id": {topic_id}, "excluded": true}}',
                    )
                ]
            )
        ),
        _FakeResponse(_FakeMessage(content="Done, I excluded that topic.", tool_calls=None)),
    ]

    def fake_completion(model, messages, tools):
        return responses.pop(0)

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    answer, actions, created_subplot_id, filtered_topic_ids = llm.answer_question(
        db_conn, "Exclude the first topic", [], [], [], []
    )

    assert answer == "Done, I excluded that topic."
    assert actions == ["set_topic_excluded"]
    assert created_subplot_id is None
    assert filtered_topic_ids is None
    assert repository.get_topics_by_ids(db_conn, [topic_id]) == []  # excluded topics are filtered out


def test_answer_question_no_tool_call_returns_answer_directly(db_conn, monkeypatch):
    monkeypatch.setattr(
        llm.litellm, "completion", lambda model, messages, tools: _FakeResponse(_FakeMessage(content="Just an answer."))
    )

    answer, actions, created_subplot_id, filtered_topic_ids = llm.answer_question(
        db_conn, "What is this story about?", [], [], [], []
    )

    assert answer == "Just an answer."
    assert actions == []
    assert created_subplot_id is None
    assert filtered_topic_ids is None


def test_answer_question_captures_created_subplot_id_from_tool_call(db_conn, monkeypatch):
    responses = [
        _FakeResponse(
            _FakeMessage(
                tool_calls=[
                    _FakeToolCall(
                        "call_1",
                        "create_subplot",
                        '{"title": "New Subplot", "summary": "A fresh thread."}',
                    )
                ]
            )
        ),
        _FakeResponse(_FakeMessage(content="Created it. Now select topics.", tool_calls=None)),
    ]

    monkeypatch.setattr(llm.litellm, "completion", lambda model, messages, tools: responses.pop(0))

    answer, actions, created_subplot_id, filtered_topic_ids = llm.answer_question(
        db_conn, "start a new subplot called New Subplot", [], [], [], []
    )

    assert actions == ["create_subplot"]
    assert created_subplot_id is not None
    assert filtered_topic_ids is None
    assert repository.get_subplot(db_conn, created_subplot_id)["title"] == "New Subplot"


def test_answer_question_captures_filtered_topic_ids_from_tool_call(db_conn, monkeypatch):
    _, topic_ids = _make_document_with_topics(db_conn)

    responses = [
        _FakeResponse(
            _FakeMessage(
                tool_calls=[
                    _FakeToolCall("call_1", "filter_topics", f'{{"topic_ids": {topic_ids}}}'),
                ]
            )
        ),
        _FakeResponse(_FakeMessage(content="Here they are.", tool_calls=None)),
    ]

    monkeypatch.setattr(llm.litellm, "completion", lambda model, messages, tools: responses.pop(0))

    answer, actions, created_subplot_id, filtered_topic_ids = llm.answer_question(
        db_conn, "show unassigned topics", [], [], [], []
    )

    assert actions == ["filter_topics"]
    assert created_subplot_id is None
    assert sorted(filtered_topic_ids) == sorted(topic_ids)


def test_build_context_includes_subplots_and_current_ids():
    subplots = [{"id": 5, "theme_id": 2, "title": "The Rivalry", "topic_ids": [11, 12]}]

    context = llm._build_context([], [], [], subplots, current_topic_id=7, current_theme_id=2)

    assert "Subplot (id=5, theme_id=2): The Rivalry - topics: [11, 12]" in context
    assert "Current topic: id=7" in context
    assert "Current theme: id=2" in context


def test_build_context_includes_add_target_lines():
    existing = llm._build_context([], [], [], [], None, None, add_target_subplot_id=9, add_target_is_new=False)
    assert "Adding topics to: subplot id=9" in existing

    new_subplot = llm._build_context([], [], [], [], None, None, add_target_subplot_id=None, add_target_is_new=True)
    assert "Adding topics to: a new subplot not created yet" in new_subplot

    neither = llm._build_context([], [], [], [], None, None)
    assert "Adding topics to" not in neither


def test_build_context_omits_current_lines_when_not_given():
    context = llm._build_context([], [], [], [], current_topic_id=None, current_theme_id=None)

    assert "Current topic" not in context
    assert "Current theme" not in context

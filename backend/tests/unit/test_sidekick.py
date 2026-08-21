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
    return theme_id, topic_ids


def test_ask_scopes_context_to_given_topic_ids(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)

    captured = {}

    def fake_answer_question(conn, question, topics, themes, encoding_rules):
        captured["question"] = question
        captured["topics"] = topics
        captured["themes"] = themes
        return "The answer.", []

    monkeypatch.setattr(llm, "answer_question", fake_answer_question)

    answer, actions = service.ask(db_conn, "What happens first?", [topic_ids[0]])

    assert answer == "The answer."
    assert actions == []
    assert captured["question"] == "What happens first?"
    assert [t["title"] for t in captured["topics"]] == ["First topic"]
    assert [t["id"] for t in captured["themes"]] == [theme_id]


def test_ask_omits_excluded_topics_even_when_explicitly_requested(db_conn, monkeypatch):
    theme_id, topic_ids = _make_document_with_topics(db_conn)
    repository.set_topic_excluded(db_conn, topic_ids[0], True)

    captured = {}
    monkeypatch.setattr(
        llm,
        "answer_question",
        lambda conn, question, topics, themes, encoding_rules: (captured.update(topics=topics) or "answer", []),
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

    answer, actions = llm.answer_question(db_conn, "Exclude the first topic", [], [], [])

    assert answer == "Done, I excluded that topic."
    assert actions == ["set_topic_excluded"]
    assert repository.get_topics_by_ids(db_conn, [topic_id]) == []  # excluded topics are filtered out


def test_answer_question_no_tool_call_returns_answer_directly(db_conn, monkeypatch):
    monkeypatch.setattr(
        llm.litellm, "completion", lambda model, messages, tools: _FakeResponse(_FakeMessage(content="Just an answer."))
    )

    answer, actions = llm.answer_question(db_conn, "What is this story about?", [], [], [])

    assert answer == "Just an answer."
    assert actions == []

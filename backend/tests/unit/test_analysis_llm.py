import json

from app.analysis import llm


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeResponse:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": _FakeMessage(content)})]


def test_manuscript_marks_heading_segments_as_chapter_breaks(monkeypatch):
    segments = [
        {"id": 1, "text": "Chapter One", "styles": [{"style_kind": "heading", "style_value": None}]},
        {"id": 2, "text": "The hero leaves home.", "styles": []},
        {"id": 3, "text": "Chapter Two", "styles": [{"style_kind": "heading", "style_value": None}]},
    ]

    captured = {}

    def fake_completion(model, messages, response_format):
        captured["manuscript"] = messages[1]["content"]
        return _FakeResponse(json.dumps({"topics": [], "themes": []}))

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    llm.extract_topics_and_themes(segments)

    lines = captured["manuscript"].splitlines()
    assert lines[0] == "[segment 1] [CHAPTER BREAK] Chapter One"
    assert lines[1] == "[segment 2] The hero leaves home."
    assert lines[2] == "[segment 3] [CHAPTER BREAK] Chapter Two"


def test_manuscript_has_no_markers_when_no_headings_present(monkeypatch):
    segments = [{"id": 1, "text": "Just prose.", "styles": []}]

    captured = {}

    def fake_completion(model, messages, response_format):
        captured["manuscript"] = messages[1]["content"]
        return _FakeResponse(json.dumps({"topics": [], "themes": []}))

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    llm.extract_topics_and_themes(segments)

    assert "CHAPTER BREAK" not in captured["manuscript"]

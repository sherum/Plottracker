from app.analysis import service
from app.analysis.models import AnalysisResult, ThemeOut, TopicOut
from app.db import repository
from app.db.stories import assign_story


def _story_document(db_conn, filename):
    document_id = repository.insert_document(
        db_conn, role="draft_script", source_path=f"/tmp/{filename}", filename=filename, source_type="txt",
        content_hash=filename,
    )
    segment_id = repository.insert_segment(db_conn, document_id=document_id, sequence_index=0, text="A scene.")
    assign_story(db_conn, document_id)
    return document_id, segment_id


def _analysis(segment_id, theme_title, existing_theme_id=None):
    return AnalysisResult(
        topics=[TopicOut(segment_start_id=segment_id, segment_end_id=segment_id, title="T", summary="s", act="opening")],
        themes=[ThemeOut(title=theme_title, summary="s", topic_indices=[0], existing_theme_id=existing_theme_id)],
    )


def test_each_story_gets_its_own_main_theme(db_conn):
    doc_a, _ = _story_document(db_conn, "alpha_1.txt")
    doc_b, _ = _story_document(db_conn, "beta_1.txt")

    story_a = repository.get_document(db_conn, doc_a)["story_id"]
    story_b = repository.get_document(db_conn, doc_b)["story_id"]

    assert repository.get_main_theme_id(db_conn, story_a) != repository.get_main_theme_id(db_conn, story_b)


def test_analysis_only_offers_and_reuses_themes_from_its_own_story(db_conn, monkeypatch):
    doc_a, segment_a = _story_document(db_conn, "alpha_1.txt")
    doc_b, segment_b = _story_document(db_conn, "beta_1.txt")
    offered = {}

    def fake_llm(segments, existing_themes=None):
        offered["themes"] = existing_themes
        return _analysis(segment_b, "Beta plot")

    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: _analysis(segment_a, "Alpha plot"))
    service.analyze_document(db_conn, doc_a)
    alpha_theme = next(t for t in repository.list_themes(db_conn) if t["title"] == "Alpha plot")

    monkeypatch.setattr(service.llm, "extract_topics_and_themes", fake_llm)
    service.analyze_document(db_conn, doc_b)

    assert offered["themes"] == []
    story_b = repository.get_document(db_conn, doc_b)["story_id"]
    beta_theme = next(t for t in repository.list_themes(db_conn) if t["title"] == "Beta plot")
    assert beta_theme["story_id"] == story_b
    assert alpha_theme["story_id"] != story_b


def test_later_edition_reuses_the_earlier_editions_themes(db_conn, monkeypatch):
    edition_1, segment_1 = _story_document(db_conn, "saga_1.txt")
    edition_2, segment_2 = _story_document(db_conn, "saga_2.txt")
    monkeypatch.setattr(service.llm, "extract_topics_and_themes", lambda segments, existing_themes=None: _analysis(segment_1, "Rebellion"))
    service.analyze_document(db_conn, edition_1)
    rebellion = next(t for t in repository.list_themes(db_conn) if t["title"] == "Rebellion")
    offered = {}

    def continue_it(segments, existing_themes=None):
        offered["ids"] = [t["id"] for t in existing_themes]
        return _analysis(segment_2, "Rebellion", existing_theme_id=rebellion["id"])

    monkeypatch.setattr(service.llm, "extract_topics_and_themes", continue_it)
    summary = service.analyze_document(db_conn, edition_2)

    assert offered["ids"] == [rebellion["id"]]
    assert summary["themes_created"] == 0
    topic = repository.list_topics(db_conn, edition_2)[-1]
    assert topic["theme_id"] == rebellion["id"]


def test_sidekick_created_subplot_belongs_to_the_active_story(db_conn):
    from app.sidekick.tools import execute_tool

    doc_a, _ = _story_document(db_conn, "alpha_1.txt")
    story_a = repository.get_document(db_conn, doc_a)["story_id"]

    created = execute_tool(db_conn, "create_subplot", {"title": "Heist", "summary": "s", "story_id": story_a})

    assert repository.get_theme(db_conn, created["theme_id"])["story_id"] == story_a


def test_lists_can_be_limited_to_one_story(db_conn):
    doc_a, _ = _story_document(db_conn, "alpha_1.txt")
    doc_b, _ = _story_document(db_conn, "beta_1.txt")
    story_a = repository.get_document(db_conn, doc_a)["story_id"]
    repository.insert_subplot(db_conn, title="A plot", summary="s", story_id=story_a)

    assert {t["story_id"] for t in repository.list_themes(db_conn, story_a)} == {story_a}
    assert [s["title"] for s in repository.list_subplots(db_conn, story_id=story_a)] == ["A plot"]
    assert repository.list_subplots(db_conn, story_id=repository.get_document(db_conn, doc_b)["story_id"]) == []
    assert [d["id"] for d in repository.list_story_documents(db_conn, story_a)] == [doc_a]


def test_stories_endpoint_lists_each_story_with_its_documents_and_main(client, db_conn):
    _story_document(db_conn, "saga_1.txt")
    _story_document(db_conn, "saga_2.txt")
    _story_document(db_conn, "other.txt")

    stories = {s["name"]: s for s in client.get("/stories").json()}

    assert stories["saga"]["document_count"] == 2
    assert stories["other"]["document_count"] == 1
    assert stories["saga"]["main_theme_id"] != stories["other"]["main_theme_id"]

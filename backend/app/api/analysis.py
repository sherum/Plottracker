import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.analysis.service import analyze_document
from app.db import repository
from app.db.connection import get_db

router = APIRouter()


class NotecardUpdate(BaseModel):
    title: str
    summary: str


class TopicActUpdate(BaseModel):
    act: Literal["opening", "conflict", "climax"] | None


class TopicMove(BaseModel):
    theme_id: int
    act: Literal["opening", "conflict", "climax"] | None


class TopicSplit(BaseModel):
    split_segment_id: int


@router.post("/documents/{document_id}/analyze")
def analyze(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return analyze_document(conn, document_id)


@router.get("/documents/{document_id}/topics")
def get_topics(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_topics(conn, document_id)


@router.get("/topics")
def get_all_topics(story_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_all_topics(conn, story_id)


@router.patch("/topics/{topic_id}")
def patch_topic(topic_id: int, request: NotecardUpdate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.update_topic(conn, topic_id, title=request.title, summary=request.summary)


@router.post("/topics/{topic_id}/exclude")
def exclude_topic(topic_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.set_topic_excluded(conn, topic_id, True)


@router.post("/topics/{topic_id}/include")
def include_topic(topic_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.set_topic_excluded(conn, topic_id, False)


@router.post("/topics/{topic_id}/unassign-theme")
def unassign_topic_theme(topic_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.unassign_topic_theme(conn, topic_id)


@router.post("/topics/{topic_id}/set-act")
def set_topic_act(topic_id: int, request: TopicActUpdate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.set_topic_act(conn, topic_id, request.act)


@router.post("/topics/{topic_id}/move")
def move_topic(topic_id: int, request: TopicMove, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.move_topic(conn, topic_id, theme_id=request.theme_id, act=request.act)


@router.get("/topics/{topic_id}/source-text")
def get_topic_source_text(topic_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return {"text": repository.get_topic_source_text(conn, topic_id)}


@router.get("/topics/{topic_id}/segments")
def get_topic_segments(topic_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.get_topic_segments(conn, topic_id)


@router.post("/topics/{topic_id}/split")
def split_topic(topic_id: int, request: TopicSplit, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.split_topic(conn, topic_id, request.split_segment_id)


@router.get("/themes")
def get_themes(story_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_themes(conn, story_id)


@router.patch("/themes/{theme_id}")
def patch_theme(theme_id: int, request: NotecardUpdate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.update_theme(conn, theme_id, title=request.title, summary=request.summary)


@router.post("/themes/{theme_id}/exclude")
def exclude_theme(theme_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.set_theme_excluded(conn, theme_id, True)


@router.post("/themes/{theme_id}/include")
def include_theme(theme_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.set_theme_excluded(conn, theme_id, False)


@router.post("/themes/{theme_id}/set-main")
def set_main_theme(theme_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    repository.set_main_theme(conn, theme_id)
    return repository.get_theme(conn, theme_id)

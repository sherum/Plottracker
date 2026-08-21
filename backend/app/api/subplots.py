import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import repository
from app.db.connection import get_db

router = APIRouter()


class SubplotCreate(BaseModel):
    title: str
    summary: str


class TopicRef(BaseModel):
    topic_id: int


@router.get("/subplots")
def list_subplots(document_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_subplots(conn, document_id)


@router.post("/subplots")
def create_subplot(request: SubplotCreate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    subplot_id = repository.insert_subplot(conn, title=request.title, summary=request.summary)
    return repository.get_subplot(conn, subplot_id)


@router.get("/subplots/{subplot_id}")
def get_subplot(subplot_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.get_subplot(conn, subplot_id)


@router.delete("/subplots/{subplot_id}")
def delete_subplot(subplot_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    repository.delete_subplot(conn, subplot_id)
    return {"deleted": subplot_id}


@router.get("/subplots/{subplot_id}/topics")
def get_subplot_topics(subplot_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_subplot_topics(conn, subplot_id)


@router.post("/subplots/{subplot_id}/topics")
def add_subplot_topic(
    subplot_id: int, request: TopicRef, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    repository.add_topic_to_subplot(conn, subplot_id, request.topic_id)
    return repository.get_subplot(conn, subplot_id)


@router.delete("/subplots/{subplot_id}/topics/{topic_id}")
def remove_subplot_topic(
    subplot_id: int, topic_id: int, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    repository.remove_topic_from_subplot(conn, subplot_id, topic_id)
    return repository.get_subplot(conn, subplot_id)


@router.post("/themes/{theme_id}/promote")
def promote_theme(theme_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    subplot_id = repository.promote_theme_to_subplot(conn, theme_id)
    return repository.get_subplot(conn, subplot_id)

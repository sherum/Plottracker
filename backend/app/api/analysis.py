import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.analysis.service import analyze_document
from app.db import repository
from app.db.connection import get_db

router = APIRouter()


class NotecardUpdate(BaseModel):
    title: str
    summary: str


@router.post("/documents/{document_id}/analyze")
def analyze(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return analyze_document(conn, document_id)


@router.get("/documents/{document_id}/topics")
def get_topics(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_topics(conn, document_id)


@router.get("/topics")
def get_all_topics(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_all_topics(conn)


@router.patch("/topics/{topic_id}")
def patch_topic(topic_id: int, request: NotecardUpdate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.update_topic(conn, topic_id, title=request.title, summary=request.summary)


@router.get("/themes")
def get_themes(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_themes(conn)


@router.patch("/themes/{theme_id}")
def patch_theme(theme_id: int, request: NotecardUpdate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.update_theme(conn, theme_id, title=request.title, summary=request.summary)

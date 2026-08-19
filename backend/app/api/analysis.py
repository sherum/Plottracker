import sqlite3

from fastapi import APIRouter, Depends

from app.analysis.service import analyze_document
from app.db import repository
from app.db.connection import get_db

router = APIRouter()


@router.post("/documents/{document_id}/analyze")
def analyze(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return analyze_document(conn, document_id)


@router.get("/documents/{document_id}/topics")
def get_topics(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_topics(conn, document_id)


@router.get("/themes")
def get_themes(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_themes(conn)

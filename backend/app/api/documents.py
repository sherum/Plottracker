import sqlite3

from fastapi import APIRouter, Depends

from app.db import repository
from app.db.connection import get_db

router = APIRouter()


@router.get("/documents")
def list_documents(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_documents(conn)


@router.get("/documents/{document_id}/segments")
def get_segments(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.get_segments(conn, document_id)


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    repository.delete_document(conn, document_id)
    return {"deleted": document_id}

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import repository
from app.db.connection import get_db
from app.ingest import service as ingest_service

router = APIRouter()


class StoryOrderUpdate(BaseModel):
    document_ids: list[int]


class DocumentRename(BaseModel):
    filename: str


@router.get("/documents")
def list_documents(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_documents(conn)


@router.patch("/documents/{document_id}")
def rename_document(document_id: int, request: DocumentRename, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        return ingest_service.rename_document(conn, document_id, request.filename)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/story/documents")
def get_story_documents(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_story_documents(conn)


@router.put("/story/documents")
def put_story_documents(request: StoryOrderUpdate, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    repository.set_story_order(conn, request.document_ids)
    return repository.list_story_documents(conn)


@router.get("/documents/{document_id}/segments")
def get_segments(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.get_segments(conn, document_id)


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    repository.delete_document(conn, document_id)
    return {"deleted": document_id}

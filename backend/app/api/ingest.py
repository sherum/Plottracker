import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.connection import get_db
from app.ingest.service import ingest_folder

router = APIRouter()


class IngestRequest(BaseModel):
    folder_path: str
    role: str


@router.post("/ingest")
def ingest(request: IngestRequest, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        return ingest_folder(conn, request.folder_path, request.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

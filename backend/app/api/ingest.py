import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.connection import get_db
from app.ingest.service import ingest_folder

router = APIRouter()


class IngestRequest(BaseModel):
    folder_path: str
    role: str


@router.post("/ingest")
def ingest(request: IngestRequest, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return ingest_folder(conn, request.folder_path, request.role)

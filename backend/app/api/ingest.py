import sqlite3

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.db.connection import get_db
from app.ingest.service import ingest_folder, upload_and_ingest

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


@router.post("/ingest/upload")
async def ingest_upload(
    file: UploadFile = File(...),
    role: str = Form(...),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    content = await file.read()
    try:
        return upload_and_ingest(conn, filename=file.filename or "", content=content, role=role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

import sqlite3

from fastapi import APIRouter, Depends

from app.db import repository
from app.db.connection import get_db

router = APIRouter()


@router.get("/stories")
def list_stories(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_stories(conn)

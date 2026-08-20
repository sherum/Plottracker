import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.connection import get_db
from app.sidekick.service import ask

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    topic_ids: list[int]


class AskResponse(BaseModel):
    answer: str


@router.post("/sidekick/ask")
def ask_sidekick(request: AskRequest, conn: sqlite3.Connection = Depends(get_db)) -> AskResponse:
    answer = ask(conn, request.question, request.topic_ids)
    return AskResponse(answer=answer)

import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db.connection import get_db
from app.sidekick.service import ask

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    topic_ids: list[int]
    current_topic_id: int | None = None
    current_theme_id: int | None = None


class AskResponse(BaseModel):
    answer: str
    actions: list[str]
    created_subplot_id: int | None = None


@router.post("/sidekick/ask")
def ask_sidekick(request: AskRequest, conn: sqlite3.Connection = Depends(get_db)) -> AskResponse:
    answer, actions, created_subplot_id = ask(
        conn,
        request.question,
        request.topic_ids,
        current_topic_id=request.current_topic_id,
        current_theme_id=request.current_theme_id,
    )
    return AskResponse(answer=answer, actions=actions, created_subplot_id=created_subplot_id)

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
    add_target_subplot_id: int | None = None
    add_target_is_new: bool = False
    story_id: int | None = None


class AskResponse(BaseModel):
    answer: str
    actions: list[str]
    created_subplot_id: int | None = None
    filtered_topic_ids: list[int] | None = None


@router.post("/sidekick/ask")
def ask_sidekick(request: AskRequest, conn: sqlite3.Connection = Depends(get_db)) -> AskResponse:
    answer, actions, created_subplot_id, filtered_topic_ids = ask(
        conn,
        request.question,
        request.topic_ids,
        current_topic_id=request.current_topic_id,
        current_theme_id=request.current_theme_id,
        add_target_subplot_id=request.add_target_subplot_id,
        add_target_is_new=request.add_target_is_new,
        story_id=request.story_id,
    )
    return AskResponse(
        answer=answer,
        actions=actions,
        created_subplot_id=created_subplot_id,
        filtered_topic_ids=filtered_topic_ids,
    )

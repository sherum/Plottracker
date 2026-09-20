import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import repository, story_links
from app.db.connection import get_db

router = APIRouter()


class StoryLink(BaseModel):
    first_story_id: int
    second_story_id: int


@router.get("/stories")
def list_stories(conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_stories(conn)


@router.post("/stories/link")
def link_stories(request: StoryLink, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """Merge the second story into the first; the first story's documents come first."""
    try:
        return {"story_id": story_links.link_stories(conn, request.first_story_id, request.second_story_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/stories/{story_id}/unlink")
def unlink_story(story_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """Detach the last-linked story; returns the id of the story that was split out."""
    try:
        return {"story_id": story_links.unlink_story(conn, story_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

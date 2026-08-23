import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import repository
from app.db.connection import get_db
from app.encoding.classifier import classify_document

router = APIRouter()


class EncodingRuleCreate(BaseModel):
    style_kind: str
    block_length: Literal["single", "multi"]
    position: Literal["chapter_start", "anywhere"]
    label: str
    description: str = ""


class EncodingRuleToggle(BaseModel):
    enabled: bool


@router.get("/encoding-rules")
def get_encoding_rules(document_id: int | None = None, conn: sqlite3.Connection = Depends(get_db)) -> list[dict]:
    return repository.list_encoding_rules(conn, document_id)


@router.post("/encoding-rules")
def create_encoding_rule(request: EncodingRuleCreate, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    rule_id = repository.insert_encoding_rule(
        conn,
        style_kind=request.style_kind,
        block_length=request.block_length,
        position=request.position,
        label=request.label,
        description=request.description,
    )
    return {"id": rule_id, **request.model_dump()}


@router.patch("/encoding-rules/{rule_id}")
def update_encoding_rule(
    rule_id: int, request: EncodingRuleCreate, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    return repository.update_encoding_rule(
        conn,
        rule_id,
        style_kind=request.style_kind,
        block_length=request.block_length,
        position=request.position,
        label=request.label,
        description=request.description,
    )


@router.delete("/encoding-rules/{rule_id}")
def delete_encoding_rule(rule_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    repository.delete_encoding_rule(conn, rule_id)
    return {"deleted": rule_id}


@router.patch("/documents/{document_id}/encoding-rules/{rule_id}")
def set_encoding_rule_enabled_for_document(
    document_id: int, rule_id: int, request: EncodingRuleToggle, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    repository.set_rule_enabled_for_document(conn, document_id, rule_id, request.enabled)
    return {"document_id": document_id, "id": rule_id, "enabled": request.enabled}


@router.post("/documents/{document_id}/classify-encoding")
def classify_encoding(document_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return classify_document(conn, document_id)

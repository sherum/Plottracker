from typing import Literal

from pydantic import BaseModel

Act = Literal["opening", "conflict", "climax"]


class TopicOut(BaseModel):
    segment_start_id: int
    segment_end_id: int
    title: str
    summary: str
    act: Act


class ThemeOut(BaseModel):
    title: str
    summary: str
    topic_indices: list[int] = []


class AnalysisResult(BaseModel):
    topics: list[TopicOut]
    themes: list[ThemeOut] = []

from pydantic import BaseModel


class TopicOut(BaseModel):
    segment_start_id: int
    segment_end_id: int
    title: str
    summary: str


class ThemeOut(BaseModel):
    title: str
    summary: str
    topic_indices: list[int] = []


class AnalysisResult(BaseModel):
    topics: list[TopicOut]
    themes: list[ThemeOut] = []

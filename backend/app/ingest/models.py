from pydantic import BaseModel


class ExtractedStyle(BaseModel):
    style_kind: str
    style_value: str | None = None


class ExtractedSegment(BaseModel):
    sequence_index: int
    text: str
    page_number: int | None = None
    paragraph_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    styles: list[ExtractedStyle] = []


class ExtractedDocument(BaseModel):
    source_type: str
    page_count: int | None = None
    segments: list[ExtractedSegment]

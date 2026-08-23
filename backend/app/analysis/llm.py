import json

import litellm

from app.analysis.models import AnalysisResult

MODEL = "openrouter/google/gemini-3.7-flash"

SYSTEM_PROMPT = """You are a story structure analyst reviewing a manuscript.

Identify topics: passages that move the plot forward, in the order they occur.
A topic is a single action or event, not a whole scene collection - a chapter
often contains several. Identify themes: groups of topics that share a
similar idea or thread. Assign each topic to one act of a three-act
structure: "opening" (setup), "conflict" (rising action), or "climax"
(resolution).

Lines marked [CHAPTER BREAK] mark the start of a new chapter, and belong to
the chapter they start, not the one before them. A topic's segment range
must never cross a chapter break - if a chapter contains several
plot-moving events, create a separate topic for each one, but every chapter
must be covered by at least one topic. A topic's segment_end_id must never
be a [CHAPTER BREAK] segment unless that same segment is also its
segment_start_id - the last segment of a chapter's final topic is the last
segment of prose before the next [CHAPTER BREAK] line, never that line
itself. If the manuscript has no [CHAPTER BREAK] markers, ignore this rule.

Respond with strict JSON only, matching this shape:
{
  "topics": [
    {"segment_start_id": int, "segment_end_id": int, "title": str, "summary": str, "act": "opening" | "conflict" | "climax"}
  ],
  "themes": [
    {"title": str, "summary": str, "topic_indices": [int], "existing_theme_id": int | null}
  ]
}

Order topics by their first appearance in the manuscript. "topic_indices" are
0-based positions into the "topics" list above.

You may be given a list of existing themes/subplots from the rest of the
story. If a group of topics continues one of them, set "existing_theme_id"
to that theme's id and reuse its title/summary rather than inventing a
near-duplicate. Only omit "existing_theme_id" (or set it null) when the
topics form a genuinely new thread not covered by any existing theme."""


def _is_chapter_break(segment: dict) -> bool:
    return any(style["style_kind"] == "heading" for style in segment.get("styles", []))


def _format_existing_themes(existing_themes: list[dict]) -> str:
    if not existing_themes:
        return ""
    lines = "\n".join(f"- id {t['id']}: {t['title']} - {t['summary']}" for t in existing_themes)
    return f"\n\nExisting themes/subplots from the rest of the story:\n{lines}"


def extract_topics_and_themes(segments: list[dict], existing_themes: list[dict] | None = None) -> AnalysisResult:
    manuscript = "\n".join(
        f"[segment {s['id']}]{' [CHAPTER BREAK]' if _is_chapter_break(s) else ''} {s['text']}" for s in segments
    )
    manuscript += _format_existing_themes(existing_themes or [])

    response = litellm.completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": manuscript},
        ],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    return AnalysisResult.model_validate(data)

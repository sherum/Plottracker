import json

import litellm

from app.analysis.models import AnalysisResult

MODEL = "openrouter/google/gemini-3.7-flash"

SYSTEM_PROMPT = """You are a story structure analyst reviewing a manuscript.

Identify topics: passages that move the plot forward, in the order they occur.
Identify themes: groups of topics that share a similar idea or thread.
Assign each topic to one act of a three-act structure: "opening" (setup),
"conflict" (rising action), or "climax" (resolution).

Respond with strict JSON only, matching this shape:
{
  "topics": [
    {"segment_start_id": int, "segment_end_id": int, "title": str, "summary": str, "act": "opening" | "conflict" | "climax"}
  ],
  "themes": [
    {"title": str, "summary": str, "topic_indices": [int]}
  ]
}

Order topics by their first appearance in the manuscript. "topic_indices" are
0-based positions into the "topics" list above."""


def extract_topics_and_themes(segments: list[dict]) -> AnalysisResult:
    manuscript = "\n".join(f"[segment {s['id']}] {s['text']}" for s in segments)

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

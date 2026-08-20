# Genre Extension Guide

Genre Writer's core — ingest, topic/theme analysis, plot viewer, review,
AI sidekick — is genre-agnostic. A genre extension customizes how the app
*interprets* a manuscript for a specific genre (sci-fi, mystery, romance,
detective, ...) without changing the core data model: documents, segments,
topics, themes, subplots.

## Status: prompt-level customization only, no plugin loader yet

There is currently no extension-loading mechanism. "Extending" today means
editing two prompt strings directly:

- `backend/app/analysis/llm.py` — `SYSTEM_PROMPT`, the instructions that
  turn a manuscript's segments into topics, themes, and act assignments.
- `backend/app/sidekick/llm.py` — `SYSTEM_PROMPT`, the instructions that
  govern how the AI sidekick answers questions and (per the AI Sidekick
  spec) rephrases dialog in a character's voice.

Both are plain Python string constants passed to `litellm.completion`.
Nothing else in the schema, API, or frontend is genre-aware.

## Intended design (not yet built)

The natural extension point is a `genre_pack` setting — an env var or
config field pointing at a directory that supplies:

- an **analysis prompt addendum**: genre-specific framing appended to the
  base `SYSTEM_PROMPT` in `app/analysis/llm.py` (e.g., a mystery pack
  might ask the model to note which topics function as clues or reveals,
  while staying inside the existing `TopicOut`/`ThemeOut` schema — no new
  columns).
- a **sidekick prompt addendum**: tone and voice guidance appended to
  `app/sidekick/llm.py`'s `SYSTEM_PROMPT`.

Keeping v1 prompt-only (no schema changes) means a genre pack can't add
new topic/theme fields yet — see "Future: schema-level extension" below.
This keeps the loader simple: load two text files, concatenate them onto
the existing prompts, done. Building that loader is the next step for
whoever picks this up; this guide describes the target shape so that work
has a concrete spec to build against.

## Building a genre extension

1. Copy `docs/CLAUDE.md.genre-template.md` into your own genre pack,
   e.g. `genres/mystery/CLAUDE.md`, and fill it in.
2. Until the loader exists, apply your pack manually: paste its Analysis
   Customization section onto the end of `SYSTEM_PROMPT` in
   `app/analysis/llm.py`, and its Sidekick Voice section onto the end of
   `SYSTEM_PROMPT` in `app/sidekick/llm.py`.
3. Ingest a sample manuscript in your genre, run Reanalyze, and check that
   the resulting topics/themes reflect your genre's framing rather than
   generic plot-forward-passage extraction.
4. Ask the sidekick a genre-flavored question and confirm the tone/voice
   guidance took effect.

## Example: a mystery genre pack

A mystery pack's analysis addendum might read:

> When identifying topics, note whether each one introduces a clue,
> plants a red herring, or delivers a reveal. Favor themes that track a
> single suspect or motive across the manuscript.

Its sidekick addendum might read:

> When asked about a clue's significance, answer only from what a
> reader would know at that point in the story — do not reveal the
> solution early.

Neither requires a new database column: both are steering the same
`title`/`summary` fields analysis already produces, just toward
mystery-relevant content.

## Future: schema-level extension

Some genres will eventually want structured fields prompt-steering can't
give them — a "suspect" or "motive" field for mystery, a "trope" field
for romance. That requires per-genre schema additions (e.g., a
`topic_metadata` key-value table) and is out of scope until the
prompt-only mechanism above exists and proves insufficient.

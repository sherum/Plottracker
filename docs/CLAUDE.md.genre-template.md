# {Genre Name} Extension for Genre Writer

Copy this file into your genre pack (e.g. `genres/{genre-name}/CLAUDE.md`)
and fill in every section. See `docs/genre-extension-guide.md` for how
this gets applied — today by hand, later by a config-driven loader.

## Genre

- Name: {e.g. Mystery}
- What makes this genre distinct for story-structure analysis purposes:
  {one or two sentences — what should the analysis look for that a
  generic pass would miss?}

## Special encodings

Per the root CLAUDE.md's Ingest feature ("the author can designate any
encoding to have special semantic meaning"), list any manuscript
conventions this genre should interpret specially — e.g. bracketed
`[CLUE]` annotations, a particular heading style marking suspect
introductions, comment-based red-herring flags.

- {encoding}: {how it should be treated}

## Analysis customization

Text to append to `SYSTEM_PROMPT` in `backend/app/analysis/llm.py`.
Stay within the existing `TopicOut` (`title`, `summary`, `act`) and
`ThemeOut` (`title`, `summary`, `topic_indices`) shapes — this is
framing guidance for the model, not a schema change.

```
{genre-specific instructions for what counts as a topic/theme, and how
to frame their titles and summaries}
```

## Sidekick voice

Text to append to `SYSTEM_PROMPT` in `backend/app/sidekick/llm.py`.
Cover tone, and any character-voice rephrasing conventions per the root
CLAUDE.md's AI Sidekick spec ("rephrase dialog using the character's
voice").

```
{genre-specific tone and behavior guidance for the sidekick}
```

## Additional metadata (future)

Fields this genre would want on topics/themes if/when schema-level
extension is supported (see "Future: schema-level extension" in the
guide). Not implemented yet — list them here so the need is on record.

- {field name}: {what it captures}

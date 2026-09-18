# Genre Writer

Turn a chaotic manuscript draft into a clear story structure. Genre Writer ingests
your drafts (.docx, .pdf, .pages, text) and notes, uses an LLM to extract topics and
themes, and shows them as notecards and a three-act plot view. An AI sidekick
answers questions about your story and edits the structure for you.

You bring your own LLM API key. Your manuscripts stay on your machine.

## Prerequisites

Either:
- uv (https://docs.astral.sh/uv/) and Node.js 20+, or
- Docker with Docker Compose

## 1. Add your credentials

    cp .env.example .env          (Windows: copy .env.example .env)

Open `.env` and set one API key. The easiest is OpenRouter, one key for many models:
get it at https://openrouter.ai/keys

    OPENROUTER_API_KEY=your-key-here

`.env` is gitignored and is never committed. Other providers work too: set the
matching key (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY) and use a model
string for that provider.

## 2. Choose your models

Set these in `.env` (both are optional; the default is openrouter/google/gemini-3.7-flash):

    ANALYSIS_MODEL=openrouter/anthropic/claude-sonnet-5
    SIDEKICK_MODEL=openrouter/google/gemini-3.7-flash

- ANALYSIS_MODEL runs ingestion and re-analysis. It reads the whole manuscript and
  must return well-formed structured output, so a more powerful model is
  recommended here.
- SIDEKICK_MODEL answers questions from short context. A fast, cheaper model is fine.

Model names are litellm strings (`provider/model`; OpenRouter models are
`openrouter/<vendor>/<model>`). Confirm exact names at https://openrouter.ai/models.
Restart the app after changing `.env`.

## 3. Start and stop

| OS      | Start                         | Stop                         |
|---------|-------------------------------|------------------------------|
| macOS   | scripts/start-mac.sh          | scripts/stop-mac.sh          |
| Linux   | scripts/start-linux.sh        | scripts/stop-linux.sh        |
| Windows | scripts\start-windows.bat     | scripts\stop-windows.bat     |

Then open http://localhost:5173 (backend API: http://localhost:8000).
Logs are written to `.backend.log` and `.frontend.log` in the repo root.
The first start installs frontend packages, which takes a minute.

### Docker alternative

    docker compose up --build

Open http://localhost:8000. Stop with `docker compose down`.

## Using it

Put draft files in `draft_scripts/` and notes in `story_notes/`, or upload them in
the app. Your database lives in `data/`. All three folders are gitignored.

## Tests

    cd backend && uv run pytest

## Extending for a genre

See docs/genre-extension-guide.md and docs/CLAUDE.md.genre-template.md.

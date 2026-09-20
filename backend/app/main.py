from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import analysis, documents, encoding, health, ingest, sidekick, stories, subplots
from app.config import REPO_ROOT

app = FastAPI(title="Genre Writer Backend")

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(subplots.router)
app.include_router(sidekick.router)
app.include_router(encoding.router)
app.include_router(stories.router)

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

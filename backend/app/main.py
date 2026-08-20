from fastapi import FastAPI

from app.api import analysis, documents, health, ingest, subplots

app = FastAPI(title="Genre Writer Backend")

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(subplots.router)

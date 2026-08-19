from fastapi import FastAPI

from app.api import documents, health, ingest

app = FastAPI(title="Genre Writer Backend")

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(documents.router)

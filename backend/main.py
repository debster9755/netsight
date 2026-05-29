import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import init_db
from backend.routers import diagnostics, capture, logs, grafana, ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="NetSight",
    description="Intelligent Network Diagnostic & Observability Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
app.include_router(capture.router, prefix="/capture", tags=["capture"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(grafana.router, prefix="/grafana", tags=["grafana"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "ai_enabled": settings.ai_enabled,
        "grafana_enabled": settings.grafana_enabled,
        "capture_interface": settings.capture_interface,
    }

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.diagnostics.runner import run_full
from backend.db.database import get_db

router = APIRouter()


class DiagnoseRequest(BaseModel):
    host: str
    run_ai: bool = False


@router.post("/")
async def diagnose(req: DiagnoseRequest):
    if not req.host.strip():
        raise HTTPException(400, "host is required")

    result = await run_full(req.host.strip())

    if req.run_ai:
        from backend.ai.analyzer import analyze
        result["ai_analysis"] = await analyze(result, "diagnostic")

    # Persist
    async with get_db() as db:
        await db.execute(
            "INSERT INTO diagnostic_runs (id, host, created_at, status, results, ai_analysis) VALUES (?, ?, ?, ?, ?, ?)",
            (
                result["id"],
                result["host"],
                result["created_at"],
                result["status"],
                json.dumps(result),
                json.dumps(result.get("ai_analysis")),
            ),
        )
        await db.commit()

    return result


@router.get("/history")
async def history(limit: int = 20):
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT id, host, created_at, status FROM diagnostic_runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
    return [dict(r) for r in rows]


@router.get("/{run_id}")
async def get_run(run_id: str):
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT results, ai_analysis FROM diagnostic_runs WHERE id = ?", (run_id,)
        )
    if not rows:
        raise HTTPException(404, "Run not found")
    row = rows[0]
    result = json.loads(row["results"])
    if row["ai_analysis"]:
        result["ai_analysis"] = json.loads(row["ai_analysis"])
    return result

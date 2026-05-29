from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Literal

from backend.ai.analyzer import analyze, AnalysisType

router = APIRouter()


class AnalyzeRequest(BaseModel):
    data: dict[str, Any]
    analysis_type: AnalysisType = "diagnostic"


@router.post("/analyze")
async def ai_analyze(req: AnalyzeRequest):
    return await analyze(req.data, req.analysis_type)


@router.get("/playbook")
async def get_playbook():
    from backend.db.database import get_db
    async with get_db() as db:
        rows = await db.execute_fetchall("SELECT * FROM resolution_playbook ORDER BY id")
    import json
    return [
        {**dict(r), "commands": json.loads(r["commands"])}
        for r in rows
    ]

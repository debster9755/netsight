import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File

from backend.core.logs.ingester import ingest
from backend.core.logs.analyzer import analyze
from backend.db.database import get_db

router = APIRouter()


@router.post("/analyze")
async def analyze_log(file: UploadFile = File(...), run_ai: bool = False):
    content = (await file.read()).decode("utf-8", errors="replace")
    ingested = ingest(content)
    analysis = analyze(ingested["entries"], ingested["format"])

    result = {
        "filename": file.filename,
        "format": ingested["format"],
        "line_count": ingested["line_count"],
        "parsed_count": ingested["parsed_count"],
        "findings": analysis["findings"],
        "stats": analysis["stats"],
    }

    if run_ai:
        from backend.ai.analyzer import analyze as ai_analyze
        result["ai_analysis"] = await ai_analyze(result, "log")

    log_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            "INSERT INTO log_analyses (id, filename, created_at, format, line_count, findings, ai_analysis) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                log_id,
                file.filename,
                datetime.now(timezone.utc).isoformat(),
                ingested["format"],
                ingested["line_count"],
                json.dumps(analysis["findings"]),
                json.dumps(result.get("ai_analysis")),
            ),
        )
        await db.commit()

    result["log_id"] = log_id
    return result

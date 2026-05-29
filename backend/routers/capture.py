import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from backend.core.capture import pcap_parser, har_parser, live
from backend.db.database import get_db

router = APIRouter()


@router.websocket("/live")
async def live_capture(
    websocket: WebSocket,
    host_filter: str | None = Query(default=None),
    port_filter: int | None = Query(default=None),
    max_packets: int = Query(default=200),
):
    await websocket.accept()
    try:
        async for packet in live.capture_stream(
            host_filter=host_filter,
            port_filter=port_filter,
            max_packets=max_packets,
        ):
            await websocket.send_json(packet)
    except WebSocketDisconnect:
        pass


@router.post("/upload")
async def upload_capture(
    file: UploadFile = File(...),
    run_ai: bool = False,
):
    content = await file.read()
    filename = file.filename or ""

    if filename.endswith(".har"):
        result = har_parser.parse_har(content)
        analysis_type = "capture"
    elif filename.endswith((".pcap", ".pcapng", ".cap")):
        result = pcap_parser.parse_pcap(content)
        analysis_type = "capture"
    else:
        # Try HAR first, then PCAP
        try:
            result = har_parser.parse_har(content)
            analysis_type = "capture"
        except Exception:
            result = pcap_parser.parse_pcap(content)
            analysis_type = "capture"

    if run_ai and result.get("ok"):
        from backend.ai.analyzer import analyze
        payload = {k: v for k, v in result.items() if k != "waterfall"}  # keep payload small
        result["ai_analysis"] = await analyze(payload, analysis_type)

    session_id = str(uuid.uuid4())
    async with get_db() as db:
        await db.execute(
            "INSERT INTO capture_sessions (id, label, created_at, packets, summary, ai_analysis) VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id,
                filename,
                datetime.now(timezone.utc).isoformat(),
                result.get("http_request_count") or result.get("entry_count") or 0,
                json.dumps(result.get("summary") or result.get("anomalies")),
                json.dumps(result.get("ai_analysis")),
            ),
        )
        await db.commit()

    result["session_id"] = session_id
    return result

from fastapi import APIRouter, Query

from backend.config import settings
from backend.core.grafana import mock, client

router = APIRouter()


@router.get("/alerts")
async def get_alerts():
    if settings.grafana_enabled:
        try:
            return await client.get_alerts()
        except Exception:
            pass
    return mock.get_alerts()


@router.get("/metrics")
async def get_metrics(window: int = Query(default=60, ge=5, le=1440)):
    if settings.grafana_enabled:
        return {"note": "Real Grafana integration active — configure dashboard_uid and panel_id"}
    return mock.get_metrics(window_minutes=window)


@router.get("/status")
async def grafana_status():
    return {
        "mode": "real" if settings.grafana_enabled else "mock",
        "grafana_url": settings.grafana_url if settings.grafana_enabled else None,
    }

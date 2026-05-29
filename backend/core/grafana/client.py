"""Real Grafana HTTP API v1 client."""
from typing import Any

import httpx

from backend.config import settings


async def get_alerts() -> list[dict[str, Any]]:
    async with _client() as c:
        resp = await c.get("/api/alertmanager/grafana/api/v2/alerts")
        resp.raise_for_status()
        raw = resp.json()
    alerts = []
    for a in raw:
        labels = a.get("labels", {})
        annotations = a.get("annotations", {})
        alerts.append({
            "id": a.get("fingerprint"),
            "name": labels.get("alertname", "Unknown"),
            "state": a.get("status", {}).get("state", "unknown"),
            "severity": labels.get("severity", "info"),
            "message": annotations.get("summary", annotations.get("description", "")),
            "panel": labels.get("grafana_panel_title", ""),
            "dashboard": labels.get("grafana_dashboard_title", ""),
            "fired_at": a.get("startsAt"),
        })
    return alerts


async def get_metrics(dashboard_uid: str, panel_id: int, window_minutes: int = 60) -> dict[str, Any]:
    """Pull a single panel's time-series data."""
    now_ms = int(__import__("time").time() * 1000)
    from_ms = now_ms - window_minutes * 60 * 1000
    async with _client() as c:
        resp = await c.get(
            f"/api/dashboards/uid/{dashboard_uid}",
        )
        resp.raise_for_status()
        return resp.json()


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.grafana_url,
        headers={"Authorization": f"Bearer {settings.grafana_api_token}"},
        timeout=10.0,
    )

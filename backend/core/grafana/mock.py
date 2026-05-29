"""Realistic mock Grafana data for MVP demo — CDN metrics time-series."""
import math
import time
from typing import Any


def get_alerts() -> list[dict[str, Any]]:
    return [
        {
            "id": 1,
            "name": "High Origin Error Rate",
            "state": "alerting",
            "severity": "critical",
            "message": "Origin 5xx rate > 5% for last 10 minutes",
            "panel": "Origin Health",
            "dashboard": "CDN Overview",
            "fired_at": "2026-05-29T09:42:00Z",
        },
        {
            "id": 2,
            "name": "Cache Miss Rate Elevated",
            "state": "alerting",
            "severity": "warning",
            "message": "Cache miss rate > 35% (current: 41%)",
            "panel": "Cache Performance",
            "dashboard": "CDN Overview",
            "fired_at": "2026-05-29T09:55:00Z",
        },
        {
            "id": 3,
            "name": "Edge Node Latency",
            "state": "ok",
            "severity": "info",
            "message": "All edge nodes within normal latency bounds",
            "panel": "Edge Latency",
            "dashboard": "CDN Overview",
            "fired_at": None,
        },
    ]


def get_metrics(window_minutes: int = 60) -> dict[str, Any]:
    """Generate realistic CDN metric time-series for the last N minutes."""
    now = int(time.time())
    step = 60  # 1-minute resolution
    points = window_minutes
    timestamps = [now - (points - i) * step for i in range(points)]

    def wave(i: int, base: float, amplitude: float, noise: float = 0.0) -> float:
        import random
        v = base + amplitude * math.sin(i / 10) + random.uniform(-noise, noise)
        return round(max(v, 0), 2)

    # Simulate an incident at 75% through the window
    incident_start = int(points * 0.65)
    incident_end = int(points * 0.85)

    def incident_spike(i: int, base: float, spike: float) -> float:
        if incident_start <= i < incident_end:
            return round(base + spike * ((i - incident_start) / (incident_end - incident_start + 1)), 2)
        return round(base + (0.2 if i >= incident_end else 0), 2)

    latency = [wave(i, 45, 8, 3) for i in range(points)]
    error_rate = [incident_spike(i, 0.8, 6.5) for i in range(points)]
    cache_hit = [round(max(min(wave(i, 78, 5, 2), 99), 40), 1) for i in range(points)]
    bandwidth_gbps = [wave(i, 2.4, 0.6, 0.1) for i in range(points)]
    req_per_sec = [wave(i, 4200, 800, 100) for i in range(points)]

    return {
        "window_minutes": window_minutes,
        "step_seconds": step,
        "series": {
            "latency_ms": {"label": "P95 Latency (ms)", "data": list(zip(timestamps, latency))},
            "error_rate_pct": {"label": "Error Rate (%)", "data": list(zip(timestamps, error_rate))},
            "cache_hit_pct": {"label": "Cache Hit Ratio (%)", "data": list(zip(timestamps, cache_hit))},
            "bandwidth_gbps": {"label": "Bandwidth (Gbps)", "data": list(zip(timestamps, bandwidth_gbps))},
            "req_per_sec": {"label": "Requests/s", "data": list(zip(timestamps, req_per_sec))},
        },
        "incident_window": {
            "start": timestamps[incident_start],
            "end": timestamps[incident_end],
            "label": "Simulated incident",
        },
    }

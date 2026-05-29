"""Parse browser HAR files — produce waterfall data + anomaly detection."""
import json
from typing import Any


def parse_har(data: bytes | str) -> dict[str, Any]:
    try:
        raw = json.loads(data) if isinstance(data, bytes) else json.loads(data)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"Invalid JSON: {exc}"}

    try:
        entries = raw["log"]["entries"]
    except (KeyError, TypeError):
        return {"ok": False, "error": "Not a valid HAR file (missing log.entries)"}

    waterfall = []
    anomalies = []
    total_size = 0
    status_counts: dict[str, int] = {}

    for entry in entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        timings = entry.get("timings", {})
        started = entry.get("startedDateTime", "")
        total_time = entry.get("time", 0)

        status = resp.get("status", 0)
        status_key = f"{status // 100}xx"
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

        size = resp.get("bodySize", 0) or 0
        total_size += max(size, 0)

        # Extract CDN / cache headers
        resp_headers = {h["name"].lower(): h["value"] for h in resp.get("headers", [])}
        req_headers = {h["name"].lower(): h["value"] for h in req.get("headers", [])}

        entry_data = {
            "url": req.get("url", ""),
            "method": req.get("method", "GET"),
            "status": status,
            "started_at": started,
            "total_ms": round(total_time, 2),
            "timings_ms": {
                "blocked": _clamp(timings.get("blocked", -1)),
                "dns": _clamp(timings.get("dns", -1)),
                "connect": _clamp(timings.get("connect", -1)),
                "ssl": _clamp(timings.get("ssl", -1)),
                "send": _clamp(timings.get("send", -1)),
                "wait": _clamp(timings.get("wait", -1)),  # TTFB
                "receive": _clamp(timings.get("receive", -1)),
            },
            "size_bytes": max(size, 0),
            "content_type": resp_headers.get("content-type", ""),
            "cache_control": resp_headers.get("cache-control", ""),
            "x_cache": resp_headers.get("x-cache", ""),
            "cdn": _detect_cdn(resp_headers),
        }
        waterfall.append(entry_data)

        # Anomaly detection
        if status >= 400:
            anomalies.append(f"HTTP {status} on {req.get('url', '')[:80]}")
        if total_time > 3000:
            anomalies.append(f"Slow request ({total_time:.0f}ms): {req.get('url', '')[:80]}")
        if _clamp(timings.get("wait", -1)) > 2000:
            anomalies.append(f"High TTFB ({timings['wait']:.0f}ms): {req.get('url', '')[:80]}")

    slow = sorted(waterfall, key=lambda e: e["total_ms"], reverse=True)[:5]

    return {
        "ok": True,
        "entry_count": len(waterfall),
        "waterfall": waterfall,
        "slowest_requests": slow,
        "status_counts": status_counts,
        "total_size_kb": round(total_size / 1024, 1),
        "anomalies": anomalies,
        "summary": _summarize(waterfall, anomalies, status_counts),
    }


def _clamp(v: float) -> float:
    return round(max(v, 0), 2)


def _detect_cdn(headers: dict) -> str | None:
    if "cf-ray" in headers:
        return "Cloudflare"
    if "x-bunny-cache" in headers:
        return "BunnyCDN"
    if "x-fastly-request-id" in headers:
        return "Fastly"
    if "x-amz-cf-id" in headers:
        return "CloudFront"
    return None


def _summarize(waterfall: list, anomalies: list, status_counts: dict) -> list[str]:
    points = [f"{len(waterfall)} requests captured"]
    if waterfall:
        avg_ms = sum(e["total_ms"] for e in waterfall) / len(waterfall)
        points.append(f"Avg load time: {avg_ms:.0f}ms")
    for code, count in status_counts.items():
        points.append(f"{count}× {code} responses")
    if anomalies:
        points.append(f"{len(anomalies)} anomalies detected")
    return points

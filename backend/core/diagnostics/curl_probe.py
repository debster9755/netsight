"""HTTP deep probe — timing breakdown + header analysis (Fiddler-like)."""
import time
from typing import Any
from urllib.parse import urlparse

import httpx


CDN_FINGERPRINTS = {
    "x-bunny-cache": "BunnyCDN",
    "x-cache": None,  # generic — check value
    "cf-ray": "Cloudflare",
    "x-fastly-request-id": "Fastly",
    "x-cache-hits": "Varnish/Fastly",
    "server: AkamaiGHost": "Akamai",
    "x-amz-cf-id": "CloudFront",
}


async def probe(url: str, follow_redirects: bool = True, timeout: float = 15.0) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    host = parsed.netloc or parsed.path

    redirect_chain = []
    timings: dict[str, float] = {}
    extensions: dict[str, Any] = {}

    try:
        async with httpx.AsyncClient(
            follow_redirects=follow_redirects,
            timeout=timeout,
            event_hooks={"request": [_on_request(timings)], "response": [_on_response(timings)]},
        ) as client:
            t0 = time.monotonic()
            response = await client.get(
                url,
                headers={"User-Agent": "NetSight/0.1 (diagnostic probe)"},
                extensions=extensions,
            )
            total_ms = round((time.monotonic() - t0) * 1000, 2)

        # Redirect chain
        for r in response.history:
            redirect_chain.append({
                "url": str(r.url),
                "status": r.status_code,
            })

        headers = dict(response.headers)
        cdn = _detect_cdn(headers)

        return {
            "url": str(response.url),
            "original_url": url,
            "host": host,
            "status_code": response.status_code,
            "ok": response.is_success,
            "redirect_chain": redirect_chain,
            "timings_ms": {
                "total": total_ms,
                **timings,
            },
            "headers": {k: v for k, v in headers.items()},
            "cdn": cdn,
            "content_type": headers.get("content-type", ""),
            "content_length": headers.get("content-length"),
            "cache_control": headers.get("cache-control"),
            "x_cache": headers.get("x-cache"),
            "age": headers.get("age"),
            "vary": headers.get("vary"),
            "server": headers.get("server"),
        }
    except httpx.TimeoutException:
        return {"url": url, "host": host, "ok": False, "error": "Request timed out"}
    except Exception as exc:
        return {"url": url, "host": host, "ok": False, "error": str(exc)}


def _on_request(timings: dict):
    async def hook(request: httpx.Request):
        timings["_req_start"] = time.monotonic()
    return hook


def _on_response(timings: dict):
    async def hook(response: httpx.Response):
        if "_req_start" in timings:
            timings["ttfb"] = round((time.monotonic() - timings["_req_start"]) * 1000, 2)
        await response.aread()
    return hook


def _detect_cdn(headers: dict) -> str | None:
    lower = {k.lower(): v.lower() for k, v in headers.items()}
    if "cf-ray" in lower:
        return "Cloudflare"
    if "x-bunny-cache" in lower or "bunny" in lower.get("server", ""):
        return "BunnyCDN"
    if "x-fastly-request-id" in lower:
        return "Fastly"
    if "x-amz-cf-id" in lower:
        return "Amazon CloudFront"
    if "x-cache-hits" in lower or "varnish" in lower.get("x-varnish", ""):
        return "Varnish"
    if "akamai" in lower.get("server", "") or "akamaighost" in lower.get("server", ""):
        return "Akamai"
    return None

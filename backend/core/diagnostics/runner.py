"""Parallel diagnostic orchestrator — runs all checks concurrently."""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.core.diagnostics import curl_probe, dns_resolver, ssl_checker, traceroute, mtr


async def run_full(host: str) -> dict[str, Any]:
    """Run DNS + SSL + HTTP + Traceroute + MTR in parallel and return structured results."""
    url = host if host.startswith("http") else f"https://{host}"
    clean_host = host.removeprefix("https://").removeprefix("http://").split("/")[0]

    dns_task = asyncio.create_task(dns_resolver.resolve(clean_host))
    ssl_task = asyncio.create_task(ssl_checker.check(clean_host))
    http_task = asyncio.create_task(curl_probe.probe(url))
    trace_task = asyncio.create_task(traceroute.trace(clean_host))
    mtr_task = asyncio.create_task(mtr.run_mtr(clean_host))

    dns_result, ssl_result, http_result, trace_result, mtr_result = await asyncio.gather(
        dns_task, ssl_task, http_task, trace_task, mtr_task
    )

    overall_status = _overall_status(dns_result, ssl_result, http_result, trace_result)

    return {
        "id": str(uuid.uuid4()),
        "host": clean_host,
        "url": url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "dns": dns_result,
        "ssl": ssl_result,
        "http": http_result,
        "traceroute": trace_result,
        "mtr": mtr_result,
        "summary": _build_summary(dns_result, ssl_result, http_result, trace_result),
    }


def _overall_status(dns, ssl, http, trace) -> str:
    if not dns.get("primary_addresses"):
        return "critical"
    if ssl.get("ok") is False:
        return "critical"
    if http.get("ok") is False:
        return "critical"
    if ssl.get("days_remaining", 999) < 14:
        return "warning"
    if trace.get("anomalies"):
        return "warning"
    if not dns.get("propagated"):
        return "warning"
    return "healthy"


def _build_summary(dns, ssl, http, trace) -> list[str]:
    points = []
    if dns.get("primary_addresses"):
        points.append(f"DNS resolves to {', '.join(dns['primary_addresses'][:2])}")
    if not dns.get("propagated"):
        points.append("DNS not consistent across resolvers — propagation may be incomplete")
    if dns.get("cdn_hint"):
        points.append(f"CDN detected: {dns['cdn_hint']}")
    if ssl.get("ok"):
        points.append(f"SSL valid · {ssl['days_remaining']}d remaining · {ssl.get('tls_version', '')}")
    elif ssl.get("ok") is False:
        points.append(f"SSL issue: {ssl.get('error', 'unknown')}")
    if http.get("ok"):
        points.append(f"HTTP {http['status_code']} · TTFB {http.get('timings_ms', {}).get('ttfb', '?')}ms · {http.get('cdn', 'no CDN detected')}")
    elif http.get("ok") is False:
        points.append(f"HTTP probe failed: {http.get('error', 'unknown')}")
    if trace.get("anomalies"):
        points.extend(trace["anomalies"])
    return points

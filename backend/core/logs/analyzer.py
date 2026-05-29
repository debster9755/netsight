"""Analyze parsed log entries — detect spikes, slow paths, IP clusters."""
from collections import Counter, defaultdict
from typing import Any


def analyze(entries: list[dict[str, Any]], fmt: str) -> dict[str, Any]:
    if not entries:
        return {"findings": [], "stats": {}}

    findings = []
    stats: dict[str, Any] = {}

    if fmt in ("nginx", "cdn_bunny", "cdn_cloudflare"):
        findings, stats = _analyze_access(entries, fmt)
    elif fmt in ("syslog", "unknown"):
        findings, stats = _analyze_syslog(entries)
    else:
        findings, stats = _analyze_access(entries, fmt)

    return {"findings": findings, "stats": stats}


def _analyze_access(entries: list[dict], fmt: str) -> tuple[list[str], dict]:
    status_counter: Counter = Counter()
    path_counter: Counter = Counter()
    ip_counter: Counter = Counter()
    slow_paths: list[tuple[float, str]] = []
    cache_counter: Counter = Counter()

    for e in entries:
        status = e.get("status")
        if status:
            status_counter[f"{status // 100}xx" if isinstance(status, int) else str(status)] += 1
        path = e.get("path") or e.get("url", "")
        if path:
            path_counter[path[:120]] += 1
        ip = e.get("ip")
        if ip:
            ip_counter[ip] += 1
        rt = e.get("request_time_s")
        if rt and rt > 1.0:
            slow_paths.append((rt, path))
        cs = e.get("cache_status")
        if cs:
            cache_counter[cs.upper()] += 1

    findings = []

    # Error rate
    total = sum(status_counter.values())
    errors_5xx = status_counter.get("5xx", 0)
    errors_4xx = status_counter.get("4xx", 0)
    if total > 0:
        error_rate = (errors_5xx + errors_4xx) / total * 100
        if error_rate > 5:
            findings.append(f"High error rate: {error_rate:.1f}% ({errors_5xx} 5xx, {errors_4xx} 4xx)")

    # Top offending IPs
    top_ips = ip_counter.most_common(5)
    if top_ips and top_ips[0][1] > total * 0.3:
        findings.append(f"Possible abuse: IP {top_ips[0][0]} sent {top_ips[0][1]} requests ({top_ips[0][1]/total*100:.0f}%)")

    # Slow endpoints
    slow_paths.sort(reverse=True)
    for rt, path in slow_paths[:3]:
        findings.append(f"Slow endpoint ({rt:.2f}s): {path[:80]}")

    # Cache miss ratio
    hits = cache_counter.get("HIT", 0)
    misses = cache_counter.get("MISS", 0)
    if hits + misses > 0:
        miss_rate = misses / (hits + misses) * 100
        if miss_rate > 40:
            findings.append(f"High cache miss rate: {miss_rate:.0f}% ({misses} misses / {hits + misses} cacheable)")

    stats = {
        "total_requests": total,
        "status_breakdown": dict(status_counter),
        "top_paths": dict(path_counter.most_common(10)),
        "top_ips": dict(top_ips),
        "cache_stats": dict(cache_counter),
        "slow_request_count": len(slow_paths),
    }

    return findings, stats


def _analyze_syslog(entries: list[dict]) -> tuple[list[str], dict]:
    severity_counter: Counter = Counter()
    process_counter: Counter = Counter()
    error_msgs: list[str] = []

    for e in entries:
        sev = e.get("severity", "info")
        severity_counter[sev] += 1
        proc = e.get("process")
        if proc:
            process_counter[proc] += 1
        if sev in ("error", "critical"):
            error_msgs.append(e.get("msg", "")[:120])

    findings = []
    total = sum(severity_counter.values())

    if severity_counter.get("critical", 0) > 0:
        findings.append(f"{severity_counter['critical']} critical severity messages detected")
    if severity_counter.get("error", 0) > 0:
        findings.append(f"{severity_counter['error']} error messages detected")
    for msg in error_msgs[:5]:
        findings.append(f"Error: {msg}")

    stats = {
        "total_lines": total,
        "severity_breakdown": dict(severity_counter),
        "top_processes": dict(process_counter.most_common(10)),
    }

    return findings, stats

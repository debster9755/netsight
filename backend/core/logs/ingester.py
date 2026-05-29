"""Log format auto-detection and parsing."""
import re
from typing import Any

from backend.core.logs.parsers import nginx, cdn, syslog


def detect_format(sample_lines: list[str]) -> str:
    for line in sample_lines[:20]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # nginx combined log: starts with IP, has [date] "METHOD
        if re.match(r'^\d+\.\d+\.\d+\.\d+ - .+\[.+\] "[A-Z]+', line):
            return "nginx"
        # Bunny pipe-delimited
        if re.match(r'^\d+\|\d{3}\|\d+\|\w+\|[\d.]+\|', line):
            return "cdn_bunny"
        # Cloudflare JSON
        try:
            import json
            obj = json.loads(line)
            if "ClientIP" in obj or "EdgeResponseStatus" in obj:
                return "cdn_cloudflare"
        except Exception:
            pass
        # syslog
        if re.match(r'^\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\S+\s+\S+', line):
            return "syslog"
    return "unknown"


def parse_lines(lines: list[str], fmt: str) -> list[dict[str, Any]]:
    parsed = []
    parser_fn = {
        "nginx": nginx.parse_line,
        "cdn_bunny": cdn.parse_line,
        "cdn_cloudflare": cdn.parse_line,
        "syslog": syslog.parse_line,
    }.get(fmt, syslog.parse_line)

    for line in lines:
        result = parser_fn(line)
        if result:
            parsed.append(result)
    return parsed


def ingest(content: str) -> dict[str, Any]:
    lines = content.splitlines()
    fmt = detect_format(lines)
    parsed = parse_lines(lines, fmt)
    return {
        "format": fmt,
        "line_count": len(lines),
        "parsed_count": len(parsed),
        "entries": parsed,
    }

"""CDN log parser — handles bunny.net, Cloudflare, and generic CDN formats."""
import re
from typing import Any

# Bunny.net: timestamp|status|bytes|cache_status|ip|url|ua|edge_location
_BUNNY_PATTERN = re.compile(
    r'(?P<ts>\d+)\|(?P<status>\d{3})\|(?P<bytes>\d+)\|'
    r'(?P<cache_status>\w+)\|(?P<ip>[\d.]+)\|(?P<url>[^\|]+)\|(?P<ua>[^\|]*)\|(?P<edge>[^\|]*)'
)

# Cloudflare JSON log line
_CF_KEYS = {"ClientIP", "ClientRequestMethod", "ClientRequestURI", "EdgeResponseStatus", "CacheCacheStatus"}

# Generic W3C extended log format (many CDNs)
_W3C_PATTERN = re.compile(
    r'(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<edge>\S+)\s+(?P<bytes>\d+)\s+(?P<ip>[\d.]+)\s+'
    r'(?P<method>\S+)\s+(?P<host>\S+)\s+(?P<path>\S+)\s+'
    r'(?P<status>\d{3})\s+(?P<cache_status>\S+)'
)


def parse_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Try bunny.net pipe-delimited
    m = _BUNNY_PATTERN.match(line)
    if m:
        return {
            "ts": int(m.group("ts")),
            "status": int(m.group("status")),
            "bytes": int(m.group("bytes")),
            "cache_status": m.group("cache_status"),
            "ip": m.group("ip"),
            "url": m.group("url"),
            "user_agent": m.group("ua"),
            "edge": m.group("edge"),
            "_format": "bunny",
        }

    # Try Cloudflare JSON
    import json
    try:
        obj = json.loads(line)
        if "ClientIP" in obj or "EdgeResponseStatus" in obj:
            return {
                "ip": obj.get("ClientIP"),
                "method": obj.get("ClientRequestMethod"),
                "path": obj.get("ClientRequestURI"),
                "status": obj.get("EdgeResponseStatus"),
                "cache_status": obj.get("CacheCacheStatus"),
                "bytes": obj.get("EdgeResponseBytes"),
                "edge": obj.get("EdgeColoCode"),
                "_format": "cloudflare",
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Try W3C
    m = _W3C_PATTERN.match(line)
    if m:
        return {
            "date": m.group("date"),
            "time": m.group("time"),
            "edge": m.group("edge"),
            "bytes": int(m.group("bytes")),
            "ip": m.group("ip"),
            "method": m.group("method"),
            "host": m.group("host"),
            "path": m.group("path"),
            "status": int(m.group("status")),
            "cache_status": m.group("cache_status"),
            "_format": "w3c",
        }

    return None

"""nginx access log parser — combined log format."""
import re
from typing import Any

# Combined log format: $remote_addr - $remote_user [$time_local] "$request" $status $bytes "$referer" "$user_agent"
_PATTERN = re.compile(
    r'(?P<ip>\S+) - (?P<user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) (?P<proto>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
    r'(?: (?P<rt>[0-9.]+))?'  # optional request_time
)


def parse_line(line: str) -> dict[str, Any] | None:
    m = _PATTERN.match(line.strip())
    if not m:
        return None
    return {
        "ip": m.group("ip"),
        "time": m.group("time"),
        "method": m.group("method"),
        "path": m.group("path"),
        "status": int(m.group("status")),
        "bytes": int(m.group("bytes")) if m.group("bytes") != "-" else 0,
        "referer": m.group("referer"),
        "user_agent": m.group("ua"),
        "request_time_s": float(m.group("rt")) if m.group("rt") else None,
        "_format": "nginx",
    }

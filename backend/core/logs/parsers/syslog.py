"""syslog / journald log parser."""
import re
from typing import Any

# RFC 3164: Nov  3 12:34:56 hostname process[pid]: message
_SYSLOG_PATTERN = re.compile(
    r'^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+'
    r'(?P<host>\S+)\s+(?P<process>[^\[:]+)(?:\[(?P<pid>\d+)\])?:\s+(?P<msg>.+)$'
)

# journald export: key=value pairs
_JOURNAL_PATTERN = re.compile(r'(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\s]*)\s+(?P<host>\S+)\s+(?P<unit>\S+)\[(?P<pid>\d+)\]:\s+(?P<msg>.+)')

SEVERITY_KEYWORDS = {
    "critical": ["critical", "crit", "emerg", "alert"],
    "error": ["error", "err", "failed", "failure"],
    "warning": ["warning", "warn", "timeout", "retry"],
}


def parse_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None

    m = _SYSLOG_PATTERN.match(line)
    if m:
        msg = m.group("msg")
        return {
            "time": f"{m.group('month')} {m.group('day')} {m.group('time')}",
            "host": m.group("host"),
            "process": m.group("process").strip(),
            "pid": m.group("pid"),
            "msg": msg,
            "severity": _classify(msg),
            "_format": "syslog",
        }

    m = _JOURNAL_PATTERN.match(line)
    if m:
        msg = m.group("msg")
        return {
            "time": m.group("ts"),
            "host": m.group("host"),
            "process": m.group("unit"),
            "pid": m.group("pid"),
            "msg": msg,
            "severity": _classify(msg),
            "_format": "journald",
        }

    # Fallback: return as raw message
    return {"msg": line, "severity": _classify(line), "_format": "raw"}


def _classify(msg: str) -> str:
    lower = msg.lower()
    for sev, keywords in SEVERITY_KEYWORDS.items():
        if any(k in lower for k in keywords):
            return sev
    return "info"

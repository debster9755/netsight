"""MTR wrapper — uses mtr --json if available, otherwise returns None."""
import asyncio
import json
from typing import Any


async def run_mtr(host: str, count: int = 10, max_hops: int = 30) -> dict[str, Any] | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "mtr", "--json", "--report", "--report-cycles", str(count),
            "--max-ttl", str(max_hops), host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode != 0:
            return None
        raw = json.loads(stdout.decode())
        return _parse_mtr(raw)
    except (FileNotFoundError, asyncio.TimeoutError, json.JSONDecodeError):
        return None


def _parse_mtr(raw: dict) -> dict[str, Any]:
    hubs = raw.get("report", {}).get("hubs", [])
    hops = []
    for hub in hubs:
        hops.append({
            "hop": hub.get("count"),
            "host": hub.get("host"),
            "loss_pct": hub.get("Loss%"),
            "sent": hub.get("Snt"),
            "avg_ms": hub.get("Avg"),
            "best_ms": hub.get("Best"),
            "worst_ms": hub.get("Wrst"),
            "stddev_ms": hub.get("StDev"),
        })
    return {
        "host": raw.get("report", {}).get("mtr", {}).get("dst"),
        "hops": hops,
        "packet_loss_any": any(h["loss_pct"] and h["loss_pct"] > 0 for h in hops),
    }

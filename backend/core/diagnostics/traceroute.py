"""Traceroute wrapper — subprocess (system traceroute) with pure-Python icmplib fallback."""
import asyncio
import platform
import re
import sys
from typing import Any


async def trace(host: str, max_hops: int = 30, timeout: int = 5) -> dict[str, Any]:
    try:
        hops = await _run_subprocess(host, max_hops, timeout)
    except FileNotFoundError:
        hops = await _icmplib_fallback(host, max_hops)
    except Exception as exc:
        return {"host": host, "ok": False, "error": str(exc), "hops": []}

    anomalies = _find_anomalies(hops)
    return {
        "host": host,
        "ok": True,
        "hop_count": len([h for h in hops if h["ip"]]),
        "max_rtt_ms": max((h["avg_ms"] for h in hops if h["avg_ms"] is not None), default=None),
        "hops": hops,
        "anomalies": anomalies,
    }


async def _run_subprocess(host: str, max_hops: int, timeout: int) -> list[dict]:
    if platform.system() == "Darwin":
        cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout), "-q", "3", host]
    else:
        cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout), "-q", "3", "-n", host]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=max_hops * (timeout + 1))
    return _parse_traceroute(stdout.decode())


def _parse_traceroute(output: str) -> list[dict]:
    hops = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("traceroute"):
            continue
        m = re.match(r"^\s*(\d+)\s+(.+)$", line)
        if not m:
            continue
        num = int(m.group(1))
        rest = m.group(2)

        if "*" in rest and re.sub(r"[\s*]", "", rest) == "":
            hops.append({"hop": num, "ip": None, "hostname": None, "rtts_ms": [], "avg_ms": None, "timeout": True})
            continue

        # Extract IP
        ip_match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", rest)
        ip = ip_match.group(1) if ip_match else None

        # Extract hostname (may differ from IP)
        hostname_match = re.match(r"([^\s(]+)\s*\(", rest)
        hostname = hostname_match.group(1) if hostname_match else ip

        # Extract RTT values
        rtt_matches = re.findall(r"(\d+(?:\.\d+)?)\s*ms", rest)
        rtts = [float(r) for r in rtt_matches]
        avg = round(sum(rtts) / len(rtts), 2) if rtts else None

        hops.append({
            "hop": num,
            "ip": ip,
            "hostname": hostname if hostname != ip else None,
            "rtts_ms": rtts,
            "avg_ms": avg,
            "timeout": False,
        })
    return hops


async def _icmplib_fallback(host: str, max_hops: int) -> list[dict]:
    """Pure-Python fallback using icmplib (requires root for ICMP)."""
    try:
        from icmplib import async_traceroute
        result = await async_traceroute(host, max_hops=max_hops, count=3, interval=0.05, timeout=2, id=None)
        hops = []
        for hop in result:
            rtts = [round(r * 1000, 2) for r in hop.rtts]
            hops.append({
                "hop": hop.distance,
                "ip": hop.address if hop.address else None,
                "hostname": None,
                "rtts_ms": rtts,
                "avg_ms": round(sum(rtts) / len(rtts), 2) if rtts else None,
                "timeout": not hop.is_alive,
            })
        return hops
    except Exception as exc:
        raise RuntimeError(f"icmplib traceroute failed: {exc}") from exc


def _find_anomalies(hops: list[dict]) -> list[str]:
    anomalies = []
    rtts = [(h["hop"], h["avg_ms"]) for h in hops if h["avg_ms"] is not None]
    for i in range(1, len(rtts)):
        prev_hop, prev_rtt = rtts[i - 1]
        curr_hop, curr_rtt = rtts[i]
        if curr_rtt > prev_rtt * 3 and curr_rtt - prev_rtt > 20:
            anomalies.append(f"High RTT jump between hop {prev_hop} ({prev_rtt}ms) → hop {curr_hop} ({curr_rtt}ms)")
    timeouts = [h["hop"] for h in hops if h.get("timeout")]
    if timeouts:
        anomalies.append(f"Timeouts (no response) at hops: {timeouts}")
    return anomalies

"""Parse PCAP files via dpkt — extract HTTP sessions and flag anomalies."""
import io
from typing import Any

import dpkt


def parse_pcap(data: bytes) -> dict[str, Any]:
    try:
        pcap = dpkt.pcap.Reader(io.BytesIO(data))
    except Exception:
        try:
            pcap = dpkt.pcapng.Reader(io.BytesIO(data))
        except Exception as exc:
            return {"ok": False, "error": f"Could not parse PCAP: {exc}"}

    sessions: dict[str, dict] = {}
    packets_total = 0
    http_requests = []
    anomalies = []
    protocols: dict[str, int] = {}

    for ts, buf in pcap:
        packets_total += 1
        try:
            eth = dpkt.ethernet.Ethernet(buf)
            if not isinstance(eth.data, dpkt.ip.IP):
                continue
            ip = eth.data
            if not isinstance(ip.data, dpkt.tcp.TCP):
                protocols["non-tcp"] = protocols.get("non-tcp", 0) + 1
                continue

            tcp = ip.data
            protocols["tcp"] = protocols.get("tcp", 0) + 1
            src = f"{_fmt_ip(ip.src)}:{tcp.sport}"
            dst = f"{_fmt_ip(ip.dst)}:{tcp.dport}"
            key = f"{src}->{dst}"

            if tcp.data:
                try:
                    req = dpkt.http.Request(tcp.data)
                    http_requests.append({
                        "ts": ts,
                        "src": src,
                        "dst": dst,
                        "method": req.method,
                        "uri": req.uri,
                        "headers": dict(req.headers),
                        "body_len": len(req.body) if req.body else 0,
                    })
                    protocols["http"] = protocols.get("http", 0) + 1
                except Exception:
                    pass
                try:
                    resp = dpkt.http.Response(tcp.data)
                    status = resp.status
                    if status.startswith("5"):
                        anomalies.append(f"HTTP 5xx at {ts:.2f}s from {dst}")
                    protocols[f"http_{status[:1]}xx"] = protocols.get(f"http_{status[:1]}xx", 0) + 1
                except Exception:
                    pass
        except Exception:
            continue

    return {
        "ok": True,
        "packets_total": packets_total,
        "http_requests": http_requests[:200],  # cap for response size
        "http_request_count": len(http_requests),
        "protocols": protocols,
        "anomalies": anomalies,
        "summary": _summarize(http_requests, anomalies),
    }


def _fmt_ip(raw: bytes) -> str:
    import socket
    return socket.inet_ntoa(raw)


def _summarize(reqs: list[dict], anomalies: list[str]) -> list[str]:
    points = [f"Captured {len(reqs)} HTTP requests"]
    methods: dict[str, int] = {}
    for r in reqs:
        methods[r["method"]] = methods.get(r["method"], 0) + 1
    for m, c in methods.items():
        points.append(f"{c}× {m}")
    if anomalies:
        points.append(f"{len(anomalies)} error responses detected")
    return points

"""Live packet capture via scapy — streams parsed packets over a WebSocket."""
import asyncio
import os
from typing import AsyncGenerator, Any

from backend.config import settings


def is_root() -> bool:
    return os.geteuid() == 0


async def capture_stream(
    iface: str | None = None,
    host_filter: str | None = None,
    port_filter: int | None = None,
    max_packets: int = 500,
) -> AsyncGenerator[dict[str, Any], None]:
    """Async generator that yields parsed packet dicts. Requires root."""
    if not is_root():
        yield {"error": "Live capture requires root. Run backend with sudo.", "ok": False}
        return

    try:
        from scapy.all import AsyncSniffer, IP, TCP, UDP, DNS, Raw
    except ImportError:
        yield {"error": "scapy not installed", "ok": False}
        return

    iface = iface or settings.capture_interface
    bpf = _build_bpf(host_filter, port_filter)

    queue: asyncio.Queue[dict | None] = asyncio.Queue(maxsize=1000)
    loop = asyncio.get_event_loop()

    def _pkt_handler(pkt):
        parsed = _parse_packet(pkt)
        if parsed:
            loop.call_soon_threadsafe(queue.put_nowait, parsed)

    sniffer = AsyncSniffer(iface=iface, filter=bpf, prn=_pkt_handler, store=False)
    sniffer.start()

    count = 0
    try:
        while count < max_packets:
            try:
                pkt = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield pkt
                count += 1
            except asyncio.TimeoutError:
                yield {"keepalive": True, "captured": count}
    finally:
        sniffer.stop()


def _build_bpf(host: str | None, port: int | None) -> str:
    parts = []
    if host:
        parts.append(f"host {host}")
    if port:
        parts.append(f"port {port}")
    return " and ".join(parts) if parts else ""


def _parse_packet(pkt) -> dict[str, Any] | None:
    try:
        from scapy.all import IP, TCP, UDP, Raw, DNSQR
        if IP not in pkt:
            return None

        proto = "TCP" if TCP in pkt else "UDP" if UDP in pkt else "OTHER"
        sport = pkt[TCP].sport if TCP in pkt else (pkt[UDP].sport if UDP in pkt else None)
        dport = pkt[TCP].dport if TCP in pkt else (pkt[UDP].dport if UDP in pkt else None)

        payload_hint = None
        if Raw in pkt:
            raw = bytes(pkt[Raw])
            if raw[:4] in (b"GET ", b"POST", b"HTTP", b"HEAD", b"PUT ", b"DELE"):
                payload_hint = raw[:80].decode("utf-8", errors="replace").split("\r\n")[0]

        return {
            "ts": float(pkt.time),
            "src": pkt[IP].src,
            "dst": pkt[IP].dst,
            "proto": proto,
            "sport": sport,
            "dport": dport,
            "len": len(pkt),
            "payload_hint": payload_hint,
            "ok": True,
        }
    except Exception:
        return None

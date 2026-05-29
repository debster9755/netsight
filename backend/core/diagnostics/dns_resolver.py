import asyncio
import time
from typing import Any

import dns.asyncresolver
import dns.resolver


SERVERS = {
    "Google": "8.8.8.8",
    "Cloudflare": "1.1.1.1",
    "Google-2": "8.8.4.4",
}


async def _resolve_one(host: str, server_name: str, server_ip: str) -> dict[str, Any]:
    resolver = dns.asyncresolver.Resolver()
    resolver.nameservers = [server_ip]
    resolver.timeout = 5
    resolver.lifetime = 5
    start = time.monotonic()
    try:
        answer = await resolver.resolve(host, "A")
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        addresses = [r.address for r in answer]
        return {
            "server": server_name,
            "server_ip": server_ip,
            "addresses": addresses,
            "ttl": answer.rrset.ttl,
            "elapsed_ms": elapsed_ms,
            "ok": True,
        }
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        return {
            "server": server_name,
            "server_ip": server_ip,
            "addresses": [],
            "ttl": None,
            "elapsed_ms": elapsed_ms,
            "ok": False,
            "error": str(exc),
        }


async def resolve(host: str) -> dict[str, Any]:
    tasks = [_resolve_one(host, name, ip) for name, ip in SERVERS.items()]
    results = await asyncio.gather(*tasks)

    # Check propagation consistency
    all_addrs = [set(r["addresses"]) for r in results if r["ok"] and r["addresses"]]
    propagated = len(set(frozenset(a) for a in all_addrs)) == 1 if all_addrs else False

    # Detect CDN by PTR / known ranges (simple fingerprint)
    primary_ips = results[0]["addresses"] if results[0]["ok"] else []

    return {
        "host": host,
        "servers": results,
        "propagated": propagated,
        "primary_addresses": primary_ips,
        "cdn_hint": _cdn_hint(primary_ips),
    }


def _cdn_hint(ips: list[str]) -> str | None:
    """Best-effort CDN detection from IP prefix."""
    if not ips:
        return None
    ip = ips[0]
    # Cloudflare: 104.16.0.0/12, 172.64.0.0/13, 198.41.128.0/17
    if ip.startswith("104.1") or ip.startswith("172.64") or ip.startswith("198.41"):
        return "Cloudflare"
    # Fastly: 151.101.0.0/16
    if ip.startswith("151.101"):
        return "Fastly"
    # Akamai: 23.32.0.0/11 (broad)
    if ip.startswith("23."):
        return "Akamai (possible)"
    # BunnyCDN doesn't have a fixed range, but pop hostnames help
    return None

import asyncio
import ssl
import socket
from datetime import datetime, timezone
from typing import Any

import OpenSSL.crypto as crypto


async def check(host: str, port: int = 443) -> dict[str, Any]:
    return await asyncio.to_thread(_check_sync, host, port)


def _check_sync(host: str, port: int) -> dict[str, Any]:
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.create_connection((host, port), timeout=10), server_hostname=host)
        cert_der = conn.getpeercert(binary_form=True)
        cipher = conn.cipher()
        tls_version = conn.version()
        conn.close()

        x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_der)
        not_after = _parse_asn1_date(x509.get_notAfter())
        not_before = _parse_asn1_date(x509.get_notBefore())
        now = datetime.now(timezone.utc)
        days_remaining = (not_after - now).days

        subject = dict(x509.get_subject().get_components())
        issuer = dict(x509.get_issuer().get_components())

        # Build SAN list
        sans = []
        for i in range(x509.get_extension_count()):
            ext = x509.get_extension(i)
            if ext.get_short_name() == b"subjectAltName":
                sans = [s.strip().replace("DNS:", "") for s in str(ext).split(",")]

        chain_depth = x509.get_extension_count()  # simplified

        return {
            "host": host,
            "port": port,
            "valid": days_remaining > 0,
            "days_remaining": days_remaining,
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "subject_cn": subject.get(b"CN", b"").decode(),
            "issuer_cn": issuer.get(b"CN", b"").decode(),
            "issuer_org": issuer.get(b"O", b"").decode(),
            "san": sans,
            "tls_version": tls_version,
            "cipher_suite": cipher[0] if cipher else None,
            "cipher_bits": cipher[2] if cipher else None,
            "ok": True,
        }
    except ssl.SSLCertVerificationError as exc:
        return {"host": host, "port": port, "ok": False, "error": f"Certificate verification failed: {exc}"}
    except Exception as exc:
        return {"host": host, "port": port, "ok": False, "error": str(exc)}


def _parse_asn1_date(raw: bytes) -> datetime:
    return datetime.strptime(raw.decode(), "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)

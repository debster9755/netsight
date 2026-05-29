"""SSL/TLS certificate checker using the cryptography library."""
import asyncio
import ssl
import socket
from datetime import datetime, timezone
from typing import Any

import certifi
from cryptography import x509
from cryptography.hazmat.backends import default_backend


async def check(host: str, port: int = 443) -> dict[str, Any]:
    return await asyncio.to_thread(_check_sync, host, port)


def _check_sync(host: str, port: int) -> dict[str, Any]:
    try:
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(certifi.where())
        conn = ctx.wrap_socket(
            socket.create_connection((host, port), timeout=10),
            server_hostname=host,
        )
        cert_der = conn.getpeercert(binary_form=True)
        cipher = conn.cipher()
        tls_version = conn.version()
        conn.close()

        cert = x509.load_der_x509_certificate(cert_der, default_backend())
        now = datetime.now(timezone.utc)
        days_remaining = (cert.not_valid_after_utc - now).days

        subject_cn = _get_attr(cert.subject, x509.NameOID.COMMON_NAME)
        issuer_cn = _get_attr(cert.issuer, x509.NameOID.COMMON_NAME)
        issuer_org = _get_attr(cert.issuer, x509.NameOID.ORGANIZATION_NAME)

        # SAN
        sans = []
        try:
            san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            sans = [name.value for name in san_ext.value]
        except x509.ExtensionNotFound:
            pass

        return {
            "host": host,
            "port": port,
            "valid": days_remaining > 0,
            "days_remaining": days_remaining,
            "not_before": cert.not_valid_before_utc.isoformat(),
            "not_after": cert.not_valid_after_utc.isoformat(),
            "subject_cn": subject_cn,
            "issuer_cn": issuer_cn,
            "issuer_org": issuer_org,
            "san": sans[:10],
            "tls_version": tls_version,
            "cipher_suite": cipher[0] if cipher else None,
            "cipher_bits": cipher[2] if cipher else None,
            "ok": True,
        }
    except ssl.SSLCertVerificationError as exc:
        return {"host": host, "port": port, "ok": False, "valid": False, "error": f"Certificate verification failed: {exc}"}
    except Exception as exc:
        return {"host": host, "port": port, "ok": False, "valid": False, "error": str(exc)}


def _get_attr(name, oid) -> str:
    try:
        return name.get_attributes_for_oid(oid)[0].value
    except (IndexError, Exception):
        return ""

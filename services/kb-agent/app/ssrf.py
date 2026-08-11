"""Outbound URL validation (SSRF guard) for kb_fetch_url."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from app.kb_service import DomainError

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}


def validate_outbound_url(url: str) -> str:
    """Return normalized URL or raise DomainError FETCH_BLOCKED."""
    raw = (url or "").strip()
    if not raw:
        raise DomainError("FETCH_BLOCKED", "url is required", status_code=400)
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise DomainError(
            "FETCH_BLOCKED",
            "only http(s) URLs are allowed",
            status_code=400,
        )
    if not parsed.hostname:
        raise DomainError("FETCH_BLOCKED", "url missing host", status_code=400)
    host = parsed.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES or host.endswith(".localhost"):
        raise DomainError("FETCH_BLOCKED", f"host blocked: {host}", status_code=400)
    # Literal IP in hostname
    try:
        ip = ipaddress.ip_address(host)
        if _is_private(ip):
            raise DomainError(
                "FETCH_BLOCKED",
                f"private or reserved address blocked: {host}",
                status_code=400,
            )
    except ValueError:
        # hostname — resolve and check all addresses
        try:
            infos = socket.getaddrinfo(host, parsed.port or None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise DomainError(
                "FETCH_BLOCKED",
                f"dns resolution failed: {host}",
                status_code=400,
            ) from exc
        if not infos:
            raise DomainError("FETCH_BLOCKED", f"dns returned no addresses: {host}", status_code=400)
        for info in infos:
            sockaddr = info[4]
            addr = sockaddr[0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if _is_private(ip):
                raise DomainError(
                    "FETCH_BLOCKED",
                    f"resolved address is private/reserved: {addr}",
                    status_code=400,
                )
    return raw


def _is_private(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )

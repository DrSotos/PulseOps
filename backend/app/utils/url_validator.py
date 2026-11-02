"""SSRF protection and URL validation utilities for PulseOps."""

import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

BLOCKED_HOSTNAMES = {
    "169.254.169.254",  # AWS/GCP/Azure link-local metadata
    "metadata.google.internal",
    "metadata.google.com",
    "100.100.100.200",  # Alibaba cloud metadata
    "instance-data",
}


class URLValidationError(Exception):
    """Raised when an endpoint URL fails safety or SSRF validation."""


def validate_url(url: str) -> str:
    """Validate a target URL for safe monitoring.

    Enforces:
    - Scheme must be http or https
    - Valid host presence
    - Blocked cloud metadata domains/IPs
    - DNS resolution
    - Rejection of loopback, private, link-local, multicast addresses unless ALLOW_PRIVATE_NETWORKS=True
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL must be a non-empty string.")

    parsed = urlparse(url.strip())

    if parsed.scheme.lower() not in ("http", "https"):
        raise URLValidationError(
            f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must contain a valid hostname or domain.")

    if hostname.lower() in BLOCKED_HOSTNAMES:
        raise URLValidationError("Access to cloud metadata endpoints is prohibited.")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    try:
        addr_info = socket.getaddrinfo(
            hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
    except socket.gaierror as e:
        raise URLValidationError(f"DNS resolution failed for hostname '{hostname}': {e}")
    except OSError as e:
        raise URLValidationError(f"Could not resolve host '{hostname}': {e}")

    if not settings.ALLOW_PRIVATE_NETWORKS:
        for item in addr_info:
            sockaddr = item[4]
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            if ip.is_loopback:
                raise URLValidationError("Requests to loopback / localhost addresses are blocked.")
            if ip.is_private:
                raise URLValidationError("Requests to private network addresses are blocked.")
            if ip.is_link_local:
                raise URLValidationError("Requests to link-local addresses are blocked.")
            if ip.is_reserved:
                raise URLValidationError("Requests to reserved IP ranges are blocked.")
            if ip.is_multicast:
                raise URLValidationError("Requests to multicast IP ranges are blocked.")
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                mapped = ip.ipv4_mapped
                if mapped.is_loopback or mapped.is_private or mapped.is_link_local:
                    raise URLValidationError("Requests to IPv4-mapped private addresses are blocked.")

    return url.strip()

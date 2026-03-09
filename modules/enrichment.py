import socket
import ipaddress
import requests
from urllib.parse import urlparse
from typing import TypedDict
from ipwhois import IPWhois


# ── Result shape ──────────────────────────────────────────────────────────────

class EnrichedResult(TypedDict):
    url: str
    status_code: int
    label: str
    priority: str
    reason: str
    ip: str
    asn_number: str
    asn_name: str
    country: str
    region: str


# ── Status code metadata ──────────────────────────────────────────────────────

JUICY_STATUS_CODES: dict[int | str, dict] = {
    200: {
        "label": "OK",
        "priority": "high",
        "reason": "Live and accessible — check title/content for admin panels, APIs, login pages",
    },
    401: {
        "label": "Unauthorized",
        "priority": "high",
        "reason": "Protected resource exists — valid target for auth bypass or credential stuffing",
    },
    403: {
        "label": "Forbidden",
        "priority": "high",
        "reason": "Resource exists but blocked — try path traversal, verb tampering, or header injection",
    },
    302: {
        "label": "Found (Redirect)",
        "priority": "high",
        "reason": "Follow redirect chain — may expose internal hostnames, staging URLs, or token leaks in Location header",
    },
    301: {
        "label": "Moved Permanently",
        "priority": "medium",
        "reason": "Canonical redirect — follow to final destination, note if redirecting to external domain",
    },
    307: {
        "label": "Temporary Redirect",
        "priority": "medium",
        "reason": "Similar to 302 — inspect Location header for internal URLs",
    },
    308: {
        "label": "Permanent Redirect",
        "priority": "medium",
        "reason": "Like 301 but method-preserving — follow chain",
    },
    400: {
        "label": "Bad Request",
        "priority": "medium",
        "reason": "Service is alive and parsing requests — may indicate API endpoint or strict input validation",
    },
    405: {
        "label": "Method Not Allowed",
        "priority": "medium",
        "reason": "Endpoint exists but rejects this method — try other HTTP verbs (GET/POST/PUT/OPTIONS)",
    },
    429: {
        "label": "Too Many Requests",
        "priority": "medium",
        "reason": "Live service with rate limiting — confirms valid target, back off and retry",
    },
    500: {
        "label": "Internal Server Error",
        "priority": "medium",
        "reason": "Server is crashing on your request — may leak stack traces, tech stack, internal paths",
    },
    503: {
        "label": "Service Unavailable",
        "priority": "medium",
        "reason": "Temporarily down or behind maintenance page — may expose internal info or be misconfigured",
    },
    204: {
        "label": "No Content",
        "priority": "low",
        "reason": "Live endpoint returning empty body — common in APIs, worth noting",
    },
    206: {
        "label": "Partial Content",
        "priority": "low",
        "reason": "Range requests supported — file serving endpoint, potentially interesting",
    },
    304: {
        "label": "Not Modified",
        "priority": "low",
        "reason": "Caching active — live resource, low priority unless cache poisoning is in scope",
    },
    501: {
        "label": "Not Implemented",
        "priority": "low",
        "reason": "Server acknowledges request but doesn't support it — confirms live host",
    },
    502: {
        "label": "Bad Gateway",
        "priority": "low",
        "reason": "Reverse proxy is live but backend is down — confirms infra exists",
    },
    404: {
        "label": "Not Found",
        "priority": "critical",
        "reason": "Combined with dangling CNAME → prime takeover candidate. Check if CNAME points to unclaimed service.",
    },
}

_FALLBACK_META = {
    "label": "Unknown",
    "priority": "unknown",
    "reason": "No metadata for this status code",
}


# ── Network helpers ───────────────────────────────────────────────────────────

def _get_ip(url: str) -> str:
    try:
        hostname = urlparse(url).hostname or ""
        return socket.gethostbyname(hostname)
    except (socket.gaierror, TypeError):
        return ""


def _get_asn_info(ip: str) -> tuple[str, str]:
    try:
        if not ip or ipaddress.ip_address(ip).is_private:
            return "", ""
        result = IPWhois(ip).lookup_rdap()
        return result.get("asn", ""), result.get("asn_description", "")
    except Exception:
        return "", ""


def _get_geolocation(ip: str) -> tuple[str, str]:
    try:
        if not ip or ipaddress.ip_address(ip).is_private:
            return "", ""
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        res.raise_for_status()
        data = res.json()
        return data.get("countryCode", ""), data.get("regionName", "")
    except Exception:
        return "", ""


# ── Public API ────────────────────────────────────────────────────────────────

def enrich(url: str, response: requests.Response) -> EnrichedResult:
    """
    Builds an EnrichedResult from a probed URL and its HTTP response.
    Always returns a complete result — missing fields default to empty string.

    Args:
        url:      The URL that was probed.
        response: The requests.Response returned by status_check.probe().
    """
    status = response.status_code
    meta = JUICY_STATUS_CODES.get(status, _FALLBACK_META)

    ip = _get_ip(url)
    asn_number, asn_name = _get_asn_info(ip)
    country, region = _get_geolocation(ip)

    return EnrichedResult(
        url=url,
        status_code=status,
        label=meta["label"],
        priority=meta["priority"],
        reason=meta["reason"],
        ip=ip,
        asn_number=asn_number,
        asn_name=asn_name,
        country=country,
        region=region,
    )
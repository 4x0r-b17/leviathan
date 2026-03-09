import requests
from typing import Generator


def _extract_subdomains(data: list[dict], domain: str) -> Generator[str, None, None]:
    seen = set()
    suffix = f".{domain}"

    for entry in data:
        for field in ("name_value", "common_name"):
            for sub in entry.get(field, "").splitlines():
                sub = sub.strip().lower()
                if (
                    sub not in seen
                    and sub.endswith(suffix)
                    and "*" not in sub
                ):
                    seen.add(sub)
                    yield sub


def _build_url(subdomain: str) -> str:
    return f"https://{subdomain}"


def fetch_crtsh(domain: str) -> Generator[str, None, None]:
    url = f"https://crt.sh/?q=%.{domain}&output=json"

    response = requests.get(
        url,
        timeout=30,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    data = response.json()  # raises ValueError if not JSON

    for subdomain in _extract_subdomains(data, domain):
        yield _build_url(subdomain)
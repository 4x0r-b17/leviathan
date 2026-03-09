from urllib.parse import urlparse
from typing import Generator


def _parse_domain(raw: str) -> tuple[str, str]:
    """
    Extracts (protocol, bare_domain) from input.
    Handles both 'https://example.com' and 'example.com'.
    """
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    protocol = parsed.scheme or "https"
    domain = parsed.netloc or parsed.path
    return protocol, domain.strip().rstrip("/")


def generate_subdomain_urls(domain: str, wordlist_path: str) -> Generator[str, None, None]:
    protocol, bare_domain = _parse_domain(domain)
    with open(wordlist_path, "r") as f:
        for line in f:
            word = line.strip()
            if word:
                yield f"{protocol}://{word}.{bare_domain}"


def generate_directory_urls(domain: str, wordlist_path: str) -> Generator[str, None, None]:
    """
    Yields candidate directory URLs from a wordlist.
    e.g. 'admin' + 'example.com' → 'https://example.com/admin'
    Does NOT make any HTTP requests.
    """
    protocol, bare_domain = _parse_domain(domain)
    with open(wordlist_path, "r") as f:
        for line in f:
            word = line.strip()
            if word:
                yield f"{protocol}://{bare_domain}/{word}"
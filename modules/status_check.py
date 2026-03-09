import requests

INTERESTING_STATUS_CODES = {
    200, 201, 204, 206,
    301, 302, 304, 307, 308,
    400, 401, 403, 405, 429,
    500, 501, 502, 503,
}

def probe(url: str, timeout: int = 5) -> requests.Response | None:
    """
    Makes a single HTTP request to `url` without following redirects.
    Falls back to http:// if the URL starts with https:// and the request fails.

    Returns:
        requests.Response if the status code is interesting, None otherwise.
    """
    def _get(target: str) -> requests.Response | None:
        try:
            res = requests.get(target, allow_redirects=False, timeout=timeout)
            if res.status_code in INTERESTING_STATUS_CODES:
                return res
            return None
        except requests.RequestException:
            return None

    result = _get(url)

    # https failed entirely (exception) — try http fallback
    if result is None and url.startswith("https://"):
        http_url = url.replace("https://", "http://", 1)
        result = _get(http_url)

    return result
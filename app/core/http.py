import requests

from app.core.config import settings

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    return session


_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = create_session()
    return _session


def http_get(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: int | None = None) -> requests.Response:
    s = get_session()
    t = timeout or settings.default_http_timeout
    merged_headers = dict(s.headers)
    if headers:
        merged_headers.update(headers)
    return s.get(url, params=params, headers=merged_headers, timeout=t)


def http_post(url: str, data: dict | None = None, json: dict | None = None,
              headers: dict | None = None, timeout: int | None = None) -> requests.Response:
    s = get_session()
    t = timeout or settings.default_http_timeout
    merged_headers = dict(s.headers)
    if headers:
        merged_headers.update(headers)
    return s.post(url, data=data, json=json, headers=merged_headers, timeout=t)

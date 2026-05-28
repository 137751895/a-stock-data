import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings
from app.core.errors import UpstreamHTTPError

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    retry = Retry(
        total=settings.default_retry_count,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = create_session()
    return _session


def http_get(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: int | None = None, provider: str = "unknown") -> requests.Response:
    s = get_session()
    t = timeout or settings.default_http_timeout
    merged_headers = dict(s.headers)
    if headers:
        merged_headers.update(headers)
    try:
        resp = s.get(url, params=params, headers=merged_headers, timeout=t)
    except requests.exceptions.Timeout:
        raise UpstreamHTTPError(f"Request timed out after {t}s: {url}", provider=provider)
    except requests.exceptions.ConnectionError:
        raise UpstreamHTTPError(f"Connection error: {url}", provider=provider)
    except requests.exceptions.RequestException as e:
        raise UpstreamHTTPError(f"Request failed: {e}", provider=provider)
    if resp.status_code != 200:
        raise UpstreamHTTPError(
            f"HTTP {resp.status_code} from {url}", provider=provider
        )
    return resp


def http_post(url: str, data: dict | None = None, json: dict | None = None,
              headers: dict | None = None, timeout: int | None = None,
              provider: str = "unknown") -> requests.Response:
    s = get_session()
    t = timeout or settings.default_http_timeout
    merged_headers = dict(s.headers)
    if headers:
        merged_headers.update(headers)
    try:
        resp = s.post(url, data=data, json=json, headers=merged_headers, timeout=t)
    except requests.exceptions.Timeout:
        raise UpstreamHTTPError(f"Request timed out after {t}s: {url}", provider=provider)
    except requests.exceptions.ConnectionError:
        raise UpstreamHTTPError(f"Connection error: {url}", provider=provider)
    except requests.exceptions.RequestException as e:
        raise UpstreamHTTPError(f"Request failed: {e}", provider=provider)
    if resp.status_code != 200:
        raise UpstreamHTTPError(
            f"HTTP {resp.status_code} from {url}", provider=provider
        )
    return resp

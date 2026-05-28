from app.core.cache import cache_get, cache_set
from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_reports

# Research reports list changes slowly (new reports appear daily, not per-minute)
# 30 minutes TTL is reasonable
REPORTS_TTL = 1800


def get_reports(code: str) -> tuple[list[dict], bool]:
    """Get research reports for a stock. Cached for 30 minutes.

    Returns (data, cached) tuple.
    """
    code = validate_code(code)

    cached = cache_get("reports", code, REPORTS_TTL)
    if cached is not None:
        return cached, True

    data = fetch_reports(code)
    cache_set("reports", code, data)
    return data, False

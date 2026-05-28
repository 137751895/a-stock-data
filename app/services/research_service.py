from app.core.cache import cache_get, cache_set
from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_reports

# Research reports list changes slowly (new reports appear daily, not per-minute)
# 30 minutes TTL is reasonable
REPORTS_TTL = 1800

VALID_CHANNELS = ("report", "announcement", "news")


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


def get_iwencai_search(query: str, channel: str = "report", size: int = 50) -> list[dict]:
    """NL semantic search via iwencai.

    Requires IWENCAI_API_KEY. Returns 403 if not configured.
    """
    from app.core.errors import ValidationError
    from app.providers.iwencai import fetch_iwencai_search, dedup_articles

    if not query or not query.strip():
        raise ValidationError("query parameter is required")
    if channel not in VALID_CHANNELS:
        raise ValidationError(f"Invalid channel: '{channel}'. Must be one of: {', '.join(VALID_CHANNELS)}")

    articles = fetch_iwencai_search(query, channel=channel, size=size)
    return dedup_articles(articles)

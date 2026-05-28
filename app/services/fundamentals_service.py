from app.core.cache import cache_get, cache_set
from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_stock_info

# stock-info changes infrequently (industry, shares, listing date)
# 10 minutes TTL balances freshness vs upstream load
STOCK_INFO_TTL = 600


def get_stock_info(code: str) -> tuple[dict, bool]:
    """Get stock fundamental info. Cached for 10 minutes.

    Returns (data, cached) tuple.
    """
    code = validate_code(code)

    cached = cache_get("stock_info", code, STOCK_INFO_TTL)
    if cached is not None:
        return cached, True

    data = fetch_stock_info(code)
    cache_set("stock_info", code, data)
    return data, False

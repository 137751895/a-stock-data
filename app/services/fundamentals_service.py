from app.core.cache import cache_get, cache_set
from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_stock_info
from app.providers.sina import fetch_financial_report

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


def get_financial_report(code: str, report_type: str = "lrb") -> list[dict]:
    """Get financial report from Sina (资产负债表/利润表/现金流量表).

    report_type: 'fzb', 'lrb', 'llb'
    """
    code = validate_code(code)
    if report_type not in ("fzb", "lrb", "llb"):
        from app.core.errors import ValidationError
        raise ValidationError(f"Invalid report_type: '{report_type}'. Must be 'fzb', 'lrb', or 'llb'")
    return fetch_financial_report(code, report_type)

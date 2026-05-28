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


def get_finance_snapshot(code: str) -> list[dict]:
    """Get 37-field quarterly finance snapshot via mootdx.

    Requires mootdx TCP connection. Returns 503 if unavailable.
    """
    from app.providers.mootdx_provider import fetch_finance_snapshot
    code = validate_code(code)
    return fetch_finance_snapshot(code)


def get_f10(code: str, category: str = "公司概况") -> dict:
    """Get F10 text data for a given category via mootdx.

    Requires mootdx TCP connection. Returns 503 if unavailable.
    """
    from app.providers.mootdx_provider import fetch_f10

    valid_categories = [
        "最新提示", "公司概况", "财务分析", "股东研究", "股本结构",
        "资本运作", "业内点评", "行业分析", "公司大事",
    ]
    code = validate_code(code)
    if category not in valid_categories:
        from app.core.errors import ValidationError
        raise ValidationError(
            f"Invalid category: '{category}'. Must be one of: {', '.join(valid_categories)}"
        )
    text = fetch_f10(code, category)
    return {"category": category, "content": text}


def get_f10_announcement(code: str) -> dict:
    """Get latest announcement summary from mootdx F10.

    Requires mootdx TCP connection. Returns 503 if unavailable.
    """
    from app.providers.mootdx_provider import fetch_f10_announcement
    code = validate_code(code)
    text = fetch_f10_announcement(code)
    return {"category": "最新提示", "content": text}

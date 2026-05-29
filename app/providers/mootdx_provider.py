"""mootdx provider — TCP-based A-stock data via mootdx library.

mootdx is an optional dependency. All functions raise DependencyUnavailableError
if the library is not installed or TCP connection fails.
"""
from app.core.errors import AppError


class DependencyUnavailableError(AppError):
    def __init__(self, message: str, provider: str = "mootdx"):
        super().__init__(
            code="DEPENDENCY_UNAVAILABLE",
            message=message,
            status_code=503,
            provider=provider,
        )


def _get_client():
    """Create a mootdx Quotes client. Raises DependencyUnavailableError on failure."""
    try:
        from mootdx.quotes import Quotes
    except ImportError:
        raise DependencyUnavailableError(
            "mootdx is not installed. Install with: pip install mootdx"
        )

    try:
        client = Quotes.factory(market="std", timeout=5)
    except Exception as e:
        raise DependencyUnavailableError(
            f"Failed to connect to mootdx server: {e}"
        )
    return client


def fetch_finance_snapshot(code: str) -> list[dict]:
    """Fetch 37-field quarterly finance snapshot via mootdx TCP.

    Returns list of dicts with keys like eps, bvps, roe, profit, income, etc.
    """
    client = _get_client()
    try:
        df = client.finance(symbol=code)
    except Exception as e:
        raise DependencyUnavailableError(f"mootdx finance query failed: {e}")

    if df is None or df.empty:
        return []

    return df.to_dict(orient="records")


def fetch_f10(code: str, category: str = "公司概况") -> str:
    """Fetch F10 text data for a given category via mootdx TCP.

    Categories: 最新提示, 公司概况, 财务分析, 股东研究, 股本结构,
                资本运作, 业内点评, 行业分析, 公司大事
    """
    client = _get_client()
    try:
        text = client.F10(symbol=code, name=category)
    except Exception as e:
        raise DependencyUnavailableError(f"mootdx F10 query failed: {e}")

    return text or ""


def fetch_f10_announcement(code: str) -> str:
    """Fetch latest announcement summary from mootdx F10 '最新提示' section."""
    return fetch_f10(code, category="最新提示")


# category mapping: human-readable → mootdx int
KLINE_CATEGORY_MAP = {
    "daily": 4,
    "weekly": 5,
    "monthly": 6,
    "1min": 7,
    "5min": 8,
    "15min": 9,
    "30min": 10,
    "60min": 11,
}


def fetch_mootdx_kline(
    code: str,
    category: str = "daily",
    offset: int = 100,
) -> list[dict]:
    """Fetch K-line bars via mootdx TCP.

    Args:
        code: 6-digit stock code.
        category: One of daily/weekly/monthly/1min/5min/15min/30min/60min.
        offset: Number of bars to return (max ~800).

    Returns list of dicts with keys: open, close, high, low, vol, amount, datetime.
    """
    cat_int = KLINE_CATEGORY_MAP.get(category)
    if cat_int is None:
        raise DependencyUnavailableError(
            f"Invalid kline category: '{category}'. "
            f"Must be one of: {', '.join(KLINE_CATEGORY_MAP)}",
        )

    client = _get_client()
    try:
        df = client.bars(symbol=code, category=cat_int, offset=offset)
    except Exception as e:
        raise DependencyUnavailableError(f"mootdx bars query failed: {e}")

    if df is None or df.empty:
        return []

    return df.to_dict(orient="records")


def fetch_mootdx_quotes(codes: list[str]) -> list[dict]:
    """Fetch real-time quotes with 5-level order book via mootdx TCP.

    Args:
        codes: List of 6-digit stock codes (e.g. ["688017", "300476"]).

    Returns list of dicts with fields: price, open, high, low, last_close,
    bid1-bid5, ask1-ask5, bid_vol1-bid_vol5, ask_vol1-ask_vol5, vol, amount, servertime.
    """
    client = _get_client()
    try:
        df = client.quotes(symbol=codes)
    except Exception as e:
        raise DependencyUnavailableError(f"mootdx quotes query failed: {e}")

    if df is None or df.empty:
        return []

    return df.to_dict(orient="records")


def fetch_mootdx_transaction(code: str, date: str = "") -> list[dict]:
    """Fetch tick-by-tick transactions via mootdx TCP.

    Args:
        code: 6-digit stock code.
        date: Date string YYYYMMDD. Empty string = today (may return empty outside trading hours).

    Returns list of dicts with keys: time, price, vol, num, buyorsell (0=buy/1=sell/2=neutral).
    """
    client = _get_client()
    kwargs: dict = {"symbol": code}
    if date:
        kwargs["date"] = date
    try:
        df = client.transaction(**kwargs)
    except Exception as e:
        raise DependencyUnavailableError(f"mootdx transaction query failed: {e}")

    if df is None or df.empty:
        return []

    return df.to_dict(orient="records")

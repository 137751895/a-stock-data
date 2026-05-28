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

from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_stock_news, fetch_global_news
from app.providers.cls import fetch_cls_telegraph


def get_stock_news(code: str) -> list[dict]:
    """Get stock-related news."""
    code = validate_code(code)
    return fetch_stock_news(code)


def get_cls_telegraph() -> list[dict]:
    """Get real-time telegraph from CLS (财联社).

    ⚠️ Deprecated (#14): cls.cn legacy API is offline; use get_global_news() instead.
    """
    return fetch_cls_telegraph()


def get_global_news() -> list[dict]:
    """Get 7x24 global financial news from Eastmoney."""
    return fetch_global_news()

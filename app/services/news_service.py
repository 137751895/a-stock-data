from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_stock_news


def get_stock_news(code: str) -> list[dict]:
    """Get stock-related news."""
    code = validate_code(code)
    return fetch_stock_news(code)

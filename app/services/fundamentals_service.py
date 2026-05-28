from app.core.normalize import normalize_code
from app.providers.eastmoney import fetch_stock_info


def get_stock_info(code: str) -> dict:
    """Get stock fundamental info."""
    code = normalize_code(code)
    return fetch_stock_info(code)

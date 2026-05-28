from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_stock_info


def get_stock_info(code: str) -> dict:
    """Get stock fundamental info."""
    code = validate_code(code)
    return fetch_stock_info(code)

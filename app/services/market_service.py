from app.core.normalize import validate_code
from app.providers.tencent import fetch_quotes


def get_quotes(codes: list[str]) -> dict[str, dict]:
    """Get real-time quotes for a list of stock codes."""
    normalized = [validate_code(c) for c in codes]
    return fetch_quotes(normalized)

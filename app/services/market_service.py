from app.core.normalize import validate_code
from app.providers.tencent import fetch_quotes


def get_quotes(codes: list[str]) -> dict[str, dict]:
    """Get real-time quotes for a list of stock codes."""
    normalized = [validate_code(c) for c in codes]
    return fetch_quotes(normalized)


def get_kline(code: str) -> dict:
    """Get K-line data with MA from Baidu Stock."""
    from app.providers.baidu import fetch_baidu_kline
    code = validate_code(code)
    return fetch_baidu_kline(code)


def get_mootdx_kline(code: str, category: str = "daily", offset: int = 100) -> list[dict]:
    """Get K-line bars via mootdx TCP.

    Requires mootdx TCP connection. Returns 503 if unavailable.
    """
    from app.providers.mootdx_provider import fetch_mootdx_kline, KLINE_CATEGORY_MAP
    code = validate_code(code)
    if category not in KLINE_CATEGORY_MAP:
        from app.core.errors import ValidationError
        raise ValidationError(
            f"Invalid category: '{category}'. Must be one of: {', '.join(KLINE_CATEGORY_MAP)}"
        )
    return fetch_mootdx_kline(code, category=category, offset=offset)

from app.core.normalize import normalize_code
from app.providers.eastmoney import fetch_reports


def get_reports(code: str) -> list[dict]:
    """Get research reports for a stock."""
    code = normalize_code(code)
    return fetch_reports(code)

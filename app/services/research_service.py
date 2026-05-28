from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_reports


def get_reports(code: str) -> list[dict]:
    """Get research reports for a stock."""
    code = validate_code(code)
    return fetch_reports(code)

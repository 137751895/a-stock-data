from app.core.normalize import validate_code
from app.providers.cninfo import fetch_announcements


def get_announcements(code: str) -> list[dict]:
    """Get announcements for a stock."""
    code = validate_code(code)
    return fetch_announcements(code)

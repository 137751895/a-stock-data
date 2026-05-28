from app.core.normalize import normalize_code
from app.providers.cninfo import fetch_announcements


def get_announcements(code: str) -> list[dict]:
    """Get announcements for a stock."""
    code = normalize_code(code)
    return fetch_announcements(code)

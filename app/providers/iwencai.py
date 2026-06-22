"""iwencai provider — NL semantic search via iwencai API.

Requires IWENCAI_API_KEY configuration. Returns ProviderAuthError if key is missing.
"""
import secrets

from app.core.config import settings
from app.core.errors import ProviderAuthError, UpstreamSchemaError
from app.core.http import http_post


def _ensure_api_key() -> str:
    """Check that iwencai API key is configured."""
    key = settings.iwencai_api_key
    if not key:
        raise ProviderAuthError(
            "IWENCAI_API_KEY is not configured. Set environment variable IWENCAI_API_KEY.",
            provider="iwencai",
        )
    return key


def _claw_headers() -> dict:
    """SkillHub 2.0 required X-Claw auth headers."""
    return {
        "X-Claw-Call-Type": "normal",
        "X-Claw-Skill-Id": "report-search",
        "X-Claw-Skill-Version": "2.0.0",
        "X-Claw-Plugin-Id": "none",
        "X-Claw-Plugin-Version": "none",
        "X-Claw-Trace-Id": secrets.token_hex(32),
    }


def fetch_iwencai_search(query: str, channel: str = "report", size: int = 50) -> list[dict]:
    """NL semantic search via iwencai API.

    Args:
        query: Natural language search query
        channel: "report" (研报) / "announcement" (公告) / "news" (新闻)
        size: Number of results (default 50)

    Returns: List of article dicts with title, publish_date, score, extra, etc.
    """
    key = _ensure_api_key()
    url = f"{settings.iwencai_base_url}/v1/comprehensive/search"
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        **_claw_headers(),
    }
    payload = {
        "channels": [channel],
        "app_id": "AIME_SKILL",
        "query": query,
        "size": size,
    }
    r = http_post(url, json=payload, headers=headers, timeout=30, provider="iwencai")
    try:
        data = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse iwencai response: {e}", provider="iwencai")

    status_code = data.get("status_code", 0)
    if status_code != 0:
        raise UpstreamSchemaError(
            f"iwencai error: {data.get('status_msg', 'unknown')}",
            provider="iwencai",
        )
    return data.get("data") or []


def dedup_articles(articles: list[dict]) -> list[dict]:
    """Deduplicate articles, keeping highest score per uid."""
    best: dict = {}
    for a in articles:
        uid = a.get("uid", "") or f"{a.get('title', '')}|{a.get('publish_date', '')}"
        score = float(a.get("score", 0))
        if uid not in best or score > float(best[uid].get("score", 0)):
            best[uid] = a
    return sorted(best.values(), key=lambda x: x.get("publish_date", ""), reverse=True)

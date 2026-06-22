from app.core.http import http_get
from app.core.errors import UpstreamSchemaError


def fetch_cls_telegraph(page_size: int = 50) -> list[dict]:
    """Fetch real-time telegraph/news from cls.cn (财联社).

    ⚠️ DEPRECATED (#14): cls.cn migrated to Next.js and the legacy public API
    (``nodeapi/telegraphList``) now returns 404. Use Eastmoney global news
    (``fetch_global_news`` / ``/global-news``) as the market-wide替代. This function
    is kept for backward compatibility but is expected to fail against the live site.
    """
    url = "https://www.cls.cn/nodeapi/telegraphList"
    params = {"rn": str(page_size), "page": "1"}
    headers = {"Referer": "https://www.cls.cn/"}
    r = http_get(url, params=params, headers=headers, provider="cls")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse CLS response: {e}", provider="cls")

    rows = []
    for item in (d.get("data") or {}).get("roll_data", []):
        rows.append({
            "title": item.get("title", "") or item.get("brief", ""),
            "content": item.get("content", "") or item.get("brief", ""),
            "time": item.get("ctime", ""),
        })
    return rows

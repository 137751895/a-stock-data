from datetime import datetime

from app.core.http import http_post
from app.core.normalize import normalize_code, to_cninfo_org_id
from app.core.errors import UpstreamSchemaError


def _cninfo_ts_to_date(ts) -> str:
    """Convert cninfo announcementTime (Unix ms) to date string."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
    return str(ts)[:10] if ts else ""


def fetch_announcements(code: str, page_size: int = 30) -> list[dict]:
    """Fetch announcements from cninfo.com.cn."""
    code = normalize_code(code)
    org_id = to_cninfo_org_id(code)

    url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    payload = {
        "stock": f"{code},{org_id}",
        "tabName": "fulltext",
        "pageSize": str(page_size),
        "pageNum": "1",
        "column": "",
        "category": "",
        "plate": "",
        "seDate": "",
        "searchkey": "",
        "secid": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.cninfo.com.cn/new/disclosure",
        "Origin": "https://www.cninfo.com.cn",
    }
    r = http_post(url, data=payload, headers=headers, provider="cninfo")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse CNInfo response: {e}", provider="cninfo")

    rows = []
    for item in d.get("announcements", []) or []:
        rows.append({
            "title": item.get("announcementTitle", ""),
            "type": item.get("announcementTypeName", ""),
            "date": _cninfo_ts_to_date(item.get("announcementTime")),
            "url": f"https://www.cninfo.com.cn/new/disclosure/detail?annoId={item.get('announcementId', '')}",
        })
    return rows

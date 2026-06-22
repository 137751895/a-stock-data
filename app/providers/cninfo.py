from datetime import datetime

from app.core.http import http_get, http_post
from app.core.normalize import normalize_code, to_cninfo_org_id
from app.core.errors import UpstreamSchemaError

# Module-level cache for cninfo 股票→orgId mapping (fetched once, reused for the process).
_CNINFO_ORGID_MAP: dict[str, str] = {}


def _cninfo_ts_to_date(ts) -> str:
    """Convert cninfo announcementTime (Unix ms) to date string."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
    return str(ts)[:10] if ts else ""


def _cninfo_orgid(code: str) -> str:
    """Resolve a stock's real cninfo orgId.

    cninfo orgIds are NOT a uniform ``gssh0{code}`` format (e.g. 601318→9900002221,
    601398→jjxt0000019, 688017→9900041602), so the hardcoded rule makes many stocks
    (especially 601xxx) return totalAnnouncement=0 (#19). Look up the official
    mapping table ``szse_stock.json`` (cached), falling back to the hardcoded rule.
    """
    global _CNINFO_ORGID_MAP
    if not _CNINFO_ORGID_MAP:
        try:
            r = http_get(
                "http://www.cninfo.com.cn/new/data/szse_stock.json",
                provider="cninfo",
            )
            _CNINFO_ORGID_MAP = {
                s["code"]: s["orgId"]
                for s in (r.json().get("stockList") or [])
                if s.get("code") and s.get("orgId")
            }
        except Exception:
            # Network/parse failure → keep map empty and fall back to hardcoded rule.
            _CNINFO_ORGID_MAP = {}
    return _CNINFO_ORGID_MAP.get(code) or to_cninfo_org_id(code)


def fetch_announcements(code: str, page_size: int = 30) -> list[dict]:
    """Fetch announcements from cninfo.com.cn."""
    code = normalize_code(code)
    org_id = _cninfo_orgid(code)

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

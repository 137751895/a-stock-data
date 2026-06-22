from app.core.http import http_get
from app.core.normalize import to_eastmoney_secid
from app.core.errors import UpstreamSchemaError

import uuid

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def fetch_stock_info(code: str) -> dict:
    """Fetch basic stock info from Eastmoney push2 API."""
    secid = to_eastmoney_secid(code)
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f57,f58,f84,f85,f127,f116,f117,f189,f43",
        "secid": secid,
    }
    r = http_get(url, params=params, provider="eastmoney")
    try:
        d = r.json().get("data", {}) or {}
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse stock info response: {e}", provider="eastmoney")
    return {
        "code": d.get("f57", ""),
        "name": d.get("f58", ""),
        "industry": d.get("f127", ""),
        "total_shares": d.get("f84", 0),
        "float_shares": d.get("f85", 0),
        "mcap": d.get("f116", 0),
        "float_mcap": d.get("f117", 0),
        "list_date": str(d.get("f189", "")),
        "price": d.get("f43", 0),
    }


def eastmoney_datacenter(report_name: str, columns: str = "ALL",
                         filter_str: str = "", page_size: int = 50,
                         sort_columns: str = "", sort_types: str = "-1") -> list[dict]:
    """Eastmoney datacenter unified query helper."""
    params = {
        "reportName": report_name,
        "columns": columns,
        "filter": filter_str,
        "pageNumber": "1",
        "pageSize": str(page_size),
        "sortColumns": sort_columns,
        "sortTypes": sort_types,
        "source": "WEB",
        "client": "WEB",
    }
    r = http_get(DATACENTER_URL, params=params, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse datacenter response: {e}", provider="eastmoney")
    if d.get("result") and d["result"].get("data"):
        return d["result"]["data"]
    return []


PDF_URL_TPL = "https://pdf.dfcfw.com/pdf/H3_{info_code}_1.pdf"


def report_pdf_url(info_code: str) -> str:
    """Build Eastmoney research report PDF download URL.

    Requires Referer: https://data.eastmoney.com/ when downloading.
    """
    return PDF_URL_TPL.format(info_code=info_code)


def fetch_reports(code: str, max_pages: int = 5) -> list[dict]:
    """Fetch research reports from Eastmoney reportapi.

    Each record is enriched with a `pdf_url` field for direct PDF download.
    The 0.3s inter-page delay is intentional rate limiting to avoid
    overloading the Eastmoney reportapi (5 pages × 0.3s = 1.2s max).
    """
    import time

    report_api = "https://reportapi.eastmoney.com/report/list"
    all_records = []
    for page in range(1, max_pages + 1):
        params = {
            "industryCode": "*", "pageSize": "100", "industry": "*",
            "rating": "*", "ratingChange": "*",
            "beginTime": "2000-01-01", "endTime": "2030-01-01",
            "pageNo": str(page), "fields": "", "qType": "0",
            "orgCode": "", "code": code, "rcode": "",
            "p": str(page), "pageNum": str(page), "pageNumber": str(page),
        }
        r = http_get(report_api, params=params,
                     headers={"Referer": "https://data.eastmoney.com/"},
                     timeout=30, provider="eastmoney")
        try:
            d = r.json()
        except Exception as e:
            raise UpstreamSchemaError(f"Failed to parse reports response: {e}", provider="eastmoney")
        rows = d.get("data") or []
        if not rows:
            break
        # Enrich each record with PDF download URL
        for row in rows:
            info_code = row.get("infoCode", "")
            if info_code:
                row["pdf_url"] = report_pdf_url(info_code)
        all_records.extend(rows)
        if page >= (d.get("TotalPage", 1) or 1):
            break
        time.sleep(0.3)
    return all_records


def fetch_fund_flow_minute(code: str) -> list[dict]:
    """Fetch minute-level fund flow from Eastmoney push2."""
    secid = to_eastmoney_secid(code)
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {
        "secid": secid,
        "klt": 1,
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
    }
    headers = {
        "Referer": "https://quote.eastmoney.com/",
        "Origin": "https://quote.eastmoney.com",
    }
    r = http_get(url, params=params, headers=headers, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse fund flow response: {e}", provider="eastmoney")

    rows = []
    for line in (d.get("data") or {}).get("klines", []):
        parts = line.split(",")
        if len(parts) >= 6:
            try:
                rows.append({
                    "time": parts[0],
                    "main_net": float(parts[1]),
                    "small_net": float(parts[2]),
                    "mid_net": float(parts[3]),
                    "large_net": float(parts[4]),
                    "super_net": float(parts[5]),
                })
            except (ValueError, TypeError):
                continue  # skip malformed lines, don't crash entire response
    return rows


def fetch_margin_trading(code: str) -> list[dict]:
    """Fetch margin trading data from Eastmoney datacenter."""
    secid = to_eastmoney_secid(code)
    market_code = secid.split(".")[0]
    market_map = {"1": "上交所", "0": "深交所"}
    market_name = market_map.get(market_code, "")

    filter_str = f'(SECURITY_CODE="{code}")'
    if market_name:
        filter_str = f'(MARKET="{market_name}"){filter_str}'

    return eastmoney_datacenter(
        report_name="RPTA_WEB_RZRQ_GGMX",
        filter_str=filter_str,
        sort_columns="TRADE_DATE",
        sort_types="-1",
        page_size=50,
    )


def fetch_stock_news(code: str, page_size: int = 20) -> list[dict]:
    """Fetch stock news from Eastmoney search API (JSONP)."""
    import json
    import re

    cb = "jQuery_news"
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    inner_params = json.dumps({
        "uid": "",
        "keyword": code,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "default",
                  "pageIndex": 1, "pageSize": page_size, "preTag": "", "postTag": ""}},
    }, separators=(',', ':'))
    params = {"cb": cb, "param": inner_params}
    headers = {"Referer": "https://so.eastmoney.com/"}

    r = http_get(url, params=params, headers=headers, provider="eastmoney")
    text = r.text
    try:
        start = text.index("(")
        end = text.rindex(")")
        json_str = text[start + 1: end]
        d = json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        raise UpstreamSchemaError(f"Failed to parse JSONP response: {e}", provider="eastmoney")

    rows = []
    # Eastmoney returns result.cmsArticleWebOld as the article list directly (not a
    # {"list": [...]} wrapper). Tolerate the legacy nested shape as a fallback. (SKILL v3.2.1 §5.1)
    raw = d.get("result", {}).get("cmsArticleWebOld", [])
    articles = raw.get("list", []) if isinstance(raw, dict) else (raw or [])
    for a in articles:
        rows.append({
            "title": re.sub(r'<[^>]+>', '', a.get("title", "")),
            "content": re.sub(r'<[^>]+>', '', a.get("content", ""))[:200],
            "time": a.get("date", ""),
            "source": a.get("mediaName", ""),
            "url": a.get("url", ""),
        })
    return rows


def fetch_billboard_records(code: str, start_date: str, end_date: str) -> list[dict]:
    """Fetch dragon tiger board records for a stock from Eastmoney datacenter."""
    return eastmoney_datacenter(
        "RPT_DAILYBILLBOARD_DETAILSNEW",
        filter_str=f"(TRADE_DATE>='{start_date}')(TRADE_DATE<='{end_date}')(SECURITY_CODE=\"{code}\")",
        page_size=50,
        sort_columns="TRADE_DATE", sort_types="-1",
    )


def fetch_billboard_seats(code: str, trade_date: str, side: str = "buy") -> list[dict]:
    """Fetch buy/sell seat details for a dragon tiger board entry.

    side: 'buy' or 'sell'
    """
    report_name = "RPT_BILLBOARD_DAILYDETAILSBUY" if side == "buy" else "RPT_BILLBOARD_DAILYDETAILSSELL"
    sort_col = "BUY" if side == "buy" else "SELL"
    return eastmoney_datacenter(
        report_name,
        filter_str=f"(TRADE_DATE='{trade_date}')(SECURITY_CODE=\"{code}\")",
        page_size=10,
        sort_columns=sort_col, sort_types="-1",
    )


def fetch_daily_billboard(trade_date: str) -> list[dict]:
    """Fetch full market dragon tiger board for a given date."""
    return eastmoney_datacenter(
        "RPT_DAILYBILLBOARD_DETAILSNEW",
        filter_str=f"(TRADE_DATE>='{trade_date}')(TRADE_DATE<='{trade_date}')",
        page_size=500,
        sort_columns="BILLBOARD_NET_AMT", sort_types="-1",
    )


def fetch_lockup_expiry(code: str) -> list[dict]:
    """Fetch lockup expiry (限售解禁) records from Eastmoney datacenter."""
    return eastmoney_datacenter(
        "RPT_LIFT_STAGE",
        filter_str=f'(SECURITY_CODE="{code}")',
        page_size=20,
        sort_columns="FREE_DATE", sort_types="-1",
    )


def fetch_industry_ranking() -> list[dict]:
    """Fetch industry sector ranking from Eastmoney push2."""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1", "pz": "100", "po": "1", "np": "1",
        "fltt": "2", "invt": "2",
        "fs": "m:90+t:2",
        "fields": "f2,f3,f4,f12,f13,f14,f104,f105,f128,f136,f140,f141,f207",
    }
    r = http_get(url, params=params, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse industry ranking response: {e}", provider="eastmoney")
    items = (d.get("data") or {}).get("diff", [])
    return items if items else []


def fetch_block_trade(code: str, page_size: int = 20) -> list[dict]:
    """Fetch block trade records from Eastmoney datacenter."""
    return eastmoney_datacenter(
        "RPT_DATA_BLOCKTRADE",
        filter_str=f'(SECURITY_CODE="{code}")',
        page_size=page_size,
        sort_columns="TRADE_DATE", sort_types="-1",
    )


def fetch_holder_num(code: str, page_size: int = 10) -> list[dict]:
    """Fetch shareholder count changes from Eastmoney datacenter."""
    return eastmoney_datacenter(
        "RPT_HOLDERNUMLATEST",
        filter_str=f'(SECURITY_CODE="{code}")',
        page_size=page_size,
        sort_columns="END_DATE", sort_types="-1",
    )


def fetch_dividend_history(code: str, page_size: int = 20) -> list[dict]:
    """Fetch dividend/bonus history from Eastmoney datacenter."""
    return eastmoney_datacenter(
        "RPT_SHAREBONUS_DET",
        filter_str=f'(SECURITY_CODE="{code}")',
        page_size=page_size,
        sort_columns="EX_DIVIDEND_DATE", sort_types="-1",
    )


def fetch_fund_flow_daily(code: str) -> list[dict]:
    """Fetch 120-day daily fund flow from Eastmoney push2his."""
    secid = to_eastmoney_secid(code)
    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        "lmt": "120",
    }
    headers = {
        "Referer": "https://quote.eastmoney.com/",
        "Origin": "https://quote.eastmoney.com",
    }
    r = http_get(url, params=params, headers=headers, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse fund flow daily response: {e}", provider="eastmoney")

    rows = []
    for line in (d.get("data") or {}).get("klines", []):
        parts = line.split(",")
        if len(parts) >= 6:
            try:
                rows.append({
                    "date": parts[0],
                    "main_net": float(parts[1]) if parts[1] != "-" else 0,
                    "small_net": float(parts[2]) if parts[2] != "-" else 0,
                    "mid_net": float(parts[3]) if parts[3] != "-" else 0,
                    "large_net": float(parts[4]) if parts[4] != "-" else 0,
                    "super_net": float(parts[5]) if parts[5] != "-" else 0,
                })
            except (ValueError, TypeError):
                continue
    return rows


def fetch_global_news(page_size: int = 50) -> list[dict]:
    """Fetch 7x24 global financial news from Eastmoney np-weblist."""
    url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"
    params = {
        "client": "web", "biz": "web_724",
        "fastColumn": "102", "sortEnd": "",
        "pageSize": str(page_size),
        "req_trace": str(uuid.uuid4()),
    }
    headers = {"Referer": "https://kuaixun.eastmoney.com/"}
    r = http_get(url, params=params, headers=headers, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse global news response: {e}", provider="eastmoney")

    rows = []
    for item in (d.get("data") or {}).get("fastNewsList", []):
        rows.append({
            "title": item.get("title", ""),
            "summary": item.get("summary", "")[:200],
            "time": item.get("showTime", ""),
        })
    return rows


def fetch_concept_blocks(code: str) -> dict:
    """Fetch a stock's board/concept membership from Eastmoney slist (spt=3).

    Replaces the dead Baidu PAE ``getrelatedblock`` endpoint (returned ResultCode
    10003 + empty array, #18). Eastmoney returns industry/concept/region boards mixed
    in a single list; the board name is self-describing. (SKILL v3.2.2 §3.3)

    Returns: {total, boards: [{name, code, change_pct, lead_stock}], concept_tags: [name...]}
    """
    secid = to_eastmoney_secid(code)
    url = "https://push2.eastmoney.com/api/qt/slist/get"
    params = {
        "fltt": "2", "invt": "2",
        "secid": secid,
        "spt": "3", "pi": "0", "pz": "200", "po": "1",
        "fields": "f12,f14,f3,f128",
    }
    headers = {"Referer": "https://quote.eastmoney.com/"}
    r = http_get(url, params=params, headers=headers, provider="eastmoney")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse concept blocks response: {e}", provider="eastmoney")

    diff = (d.get("data") or {}).get("diff") or {}
    items = diff.values() if isinstance(diff, dict) else diff
    boards = []
    for it in items:
        boards.append({
            "name": it.get("f14", ""),         # 板块名
            "code": it.get("f12", ""),         # BK 板块代码
            "change_pct": it.get("f3", ""),    # 板块当日涨跌幅
            "lead_stock": it.get("f128", ""),  # 板块龙头股
        })
    return {
        "total": len(boards),
        "boards": boards,
        "concept_tags": [b["name"] for b in boards],
    }

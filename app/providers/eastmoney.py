from app.core.http import http_get
from app.core.normalize import to_eastmoney_secid
from app.core.errors import UpstreamSchemaError

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


def fetch_reports(code: str, max_pages: int = 5) -> list[dict]:
    """Fetch research reports from Eastmoney reportapi."""
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
    articles = d.get("result", {}).get("cmsArticleWebOld", {}).get("list", [])
    for a in articles:
        rows.append({
            "title": re.sub(r'<[^>]+>', '', a.get("title", "")),
            "content": re.sub(r'<[^>]+>', '', a.get("content", ""))[:200],
            "time": a.get("date", ""),
            "source": a.get("mediaName", ""),
            "url": a.get("url", ""),
        })
    return rows

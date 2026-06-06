from app.core.http import http_get
from app.core.errors import UpstreamSchemaError


def fetch_baidu_kline(code: str) -> dict:
    """Fetch K-line data with MA5/MA10/MA20 from Baidu Stock (百度股市通).

    Returns: {keys: [...], rows: [...]}
    """
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {
        "all": "1", "isIndex": "false", "isBk": "false", "isBlock": "false",
        "isFutures": "false", "isStock": "true", "newFormat": "1",
        "group": "quotation_kline_ab", "finClientType": "pc",
        "code": code, "start_time": "", "ktype": "1",
    }
    headers = {
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    r = http_get(url, params=params, headers=headers, provider="baidu")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse Baidu kline response: {e}", provider="baidu")

    result = d.get("Result", {})
    md = result.get("newMarketData", {})
    keys = md.get("keys", [])
    raw_rows = md.get("marketData", "").split(";")

    rows = []
    for raw in raw_rows:
        if not raw.strip():
            continue
        parts = raw.split(",")
        if len(parts) >= len(keys):
            row = {}
            for i, key in enumerate(keys):
                row[key] = parts[i]
            rows.append(row)
    return {"keys": keys, "rows": rows}

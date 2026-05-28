from app.core.http import http_get
from app.core.errors import UpstreamSchemaError

_BAIDU_PAE_HEADERS = {
    "Accept": "application/vnd.finance-web.v1+json",
    "Origin": "https://gushitong.baidu.com",
    "Referer": "https://gushitong.baidu.com/",
}


def fetch_concept_blocks(code: str) -> dict:
    """Fetch concept block classification from Baidu Stock (百度股市通).

    Returns: {industry: [...], concept: [...], region: [...], concept_tags: [...]}
    """
    url = "https://finance.pae.baidu.com/api/getrelatedblock"
    params = {
        "code": code,
        "market": "ab",
        "typeCode": "all",
        "finClientType": "pc",
    }
    r = http_get(url, params=params, headers=_BAIDU_PAE_HEADERS, provider="baidu")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse Baidu concept response: {e}", provider="baidu")

    # ResultCode can be int 0 or string "0"
    if str(d.get("ResultCode", -1)) != "0":
        raise UpstreamSchemaError(f"Baidu PAE error: ResultCode={d.get('ResultCode')}", provider="baidu")

    result: dict = {"industry": [], "concept": [], "region": [], "concept_tags": []}
    for block in d.get("Result", []):
        block_type = block.get("type", "")
        for item in block.get("list", []):
            entry = {
                "name": item.get("name", ""),
                "change_pct": item.get("increase", ""),
                "desc": item.get("desc", ""),
            }
            if "行业" in block_type:
                result["industry"].append(entry)
            elif "概念" in block_type:
                result["concept"].append(entry)
                result["concept_tags"].append(entry["name"])
            elif "地域" in block_type:
                result["region"].append(entry)
    return result


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

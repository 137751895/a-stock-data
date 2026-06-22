
from app.core.http import http_get
from app.core.errors import UpstreamSchemaError


def fetch_eps_forecast(code: str) -> dict:
    """Fetch EPS forecast from THS (10jqka.com.cn).

    Returns raw HTML text for parsing.
    Raises UpstreamHTTPError on non-200 or network errors.
    """
    url = f"https://basic.10jqka.com.cn/new/{code}/worth.html"
    headers = {
        "Referer": "https://basic.10jqka.com.cn/",
    }
    r = http_get(url, headers=headers, provider="ths")
    r.encoding = "gbk"
    return {"html": r.text}


def fetch_hot_stocks(date: str) -> list[dict]:
    """Fetch THS hot/strong stocks with reason tags for a given date.

    Args:
        date: YYYY-MM-DD format

    Returns: List of dicts with code, name, reason, close, change_pct, etc.
    """
    url = (
        f"http://zx.10jqka.com.cn/event/api/getharden/"
        f"date/{date}/orderby/date/orderway/desc/charset/GBK/"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "Chrome/117.0.0.0 Safari/537.36"
        ),
    }
    r = http_get(url, headers=headers, provider="ths")
    try:
        data = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse THS hot stocks response: {e}", provider="ths")

    errocode = data.get("errocode", 0)
    if errocode != 0:
        raise UpstreamSchemaError(
            f"THS hot stocks error: {data.get('errormsg', 'unknown')}",
            provider="ths",
        )

    return data.get("data") or []


def fetch_northbound_realtime() -> dict:
    """Fetch northbound capital realtime minute-level flow from THS (hexin.cn).

    Returns: {time: [...], hgt: [...], sgt: [...]}
    """
    url = "https://data.hexin.cn/market/hsgtApi/method/dayChart/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "Chrome/117.0.0.0 Safari/537.36"
        ),
        "Host": "data.hexin.cn",
        "Referer": "https://data.hexin.cn/",
    }
    r = http_get(url, headers=headers, provider="ths")
    try:
        data = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse THS northbound response: {e}", provider="ths")

    return {
        "time": data.get("time", []),
        "hgt": data.get("hgt", []),
        "sgt": data.get("sgt", []),
    }

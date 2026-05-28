
from app.core.http import http_get


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


from app.core.http import http_get


def fetch_eps_forecast(code: str) -> dict:
    """Fetch EPS forecast from THS (10jqka.com.cn).

    Returns raw HTML text for parsing.
    """
    url = f"https://basic.10jqka.com.cn/new/{code}/worth.html"
    headers = {
        "Referer": "https://basic.10jqka.com.cn/",
    }
    r = http_get(url, headers=headers)
    r.encoding = "gbk"
    return {"html": r.text, "status_code": r.status_code}

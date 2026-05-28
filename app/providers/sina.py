from app.core.http import http_get
from app.core.errors import UpstreamSchemaError


def fetch_financial_report(code: str, report_type: str = "lrb") -> list[dict]:
    """Fetch financial report from Sina Finance (新浪财报三表).

    report_type: 'fzb' (资产负债表), 'lrb' (利润表), 'llb' (现金流量表)
    Returns: list of financial records
    """
    prefix = "sh" if code.startswith("6") else "sz"
    paper_code = f"{prefix}{code}"
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"
    params = {
        "paperCode": paper_code,
        "source": report_type,
        "type": "0",
        "page": "1",
        "num": "20",
    }
    r = http_get(url, params=params, provider="sina")
    try:
        d = r.json()
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse Sina financial report response: {e}", provider="sina")

    result = d.get("result", {}).get("data", {})
    items = result.get(report_type, [])
    return items if isinstance(items, list) else []

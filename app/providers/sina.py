from app.core.http import http_get
from app.core.errors import UpstreamSchemaError


def fetch_financial_report(code: str, report_type: str = "lrb", num: int = 8) -> list[dict]:
    """Fetch financial report from Sina Finance (新浪财报三表).

    report_type: 'fzb' (资产负债表), 'lrb' (利润表), 'llb' (现金流量表)
    num: number of most recent reporting periods to return (default 8)

    Sina's actual structure is ``result.data.report_list`` — a dict keyed by reporting
    period (e.g. '20260331'); each period's ``data`` field holds the line items
    ``[{item_title, item_value, item_tongbi}]``. The legacy ``result.data.{report_type}``
    access path permanently returned empty. (SKILL v3.2.1 §6.4)

    Returns: list of records (one per period, newest first):
             {"报告期": "2026-03-31", "<科目>": "<值>", "<科目>_同比": <同比>, ...}
    """
    prefix = "sh" if code.startswith("6") else "sz"
    paper_code = f"{prefix}{code}"
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"
    params = {
        "paperCode": paper_code,
        "source": report_type,
        "type": "0",
        "page": "1",
        "num": str(num),
    }
    r = http_get(url, params=params, provider="sina")
    try:
        report_list = r.json().get("result", {}).get("data", {}).get("report_list", {}) or {}
    except Exception as e:
        raise UpstreamSchemaError(f"Failed to parse Sina financial report response: {e}", provider="sina")

    rows = []
    for period in sorted(report_list.keys(), reverse=True)[:num]:
        obj = report_list[period] or {}
        rec = {"报告期": f"{period[:4]}-{period[4:6]}-{period[6:8]}"}
        for it in obj.get("data", []) or []:
            title = it.get("item_title", "")
            if not title or it.get("item_value") is None:
                continue
            rec[title] = it.get("item_value")
            tongbi = it.get("item_tongbi")
            if tongbi not in (None, ""):
                rec[title + "_同比"] = tongbi
        rows.append(rec)
    return rows

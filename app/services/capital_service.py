from app.core.normalize import validate_code
from app.providers.eastmoney import fetch_fund_flow_minute, fetch_margin_trading


def get_fund_flow_minute(code: str) -> list[dict]:
    """Get minute-level fund flow for a stock."""
    code = validate_code(code)
    return fetch_fund_flow_minute(code)


def get_margin_trading(code: str) -> list[dict]:
    """Get margin trading data for a stock.

    Normalizes Eastmoney datacenter raw fields to SKILL.md semantics:
    date, rzye, rzmre, rzche, rqye, rqmcl, rqchl, rzrqye
    """
    code = validate_code(code)
    raw_rows = fetch_margin_trading(code)
    rows = []
    for row in raw_rows:
        rows.append({
            "date": str(row.get("DATE", row.get("TRADE_DATE", "")))[:10],
            "rzye": row.get("RZYE", 0),       # 融资余额(元)
            "rzmre": row.get("RZMRE", 0),      # 融资买入额
            "rzche": row.get("RZCHE", 0),      # 融资偿还额
            "rqye": row.get("RQYE", 0),        # 融券余额(元)
            "rqmcl": row.get("RQMCL", 0),      # 融券卖出量
            "rqchl": row.get("RQCHL", 0),      # 融券偿还量
            "rzrqye": row.get("RZRQYE", 0),    # 融资融券余额合计
        })
    return rows

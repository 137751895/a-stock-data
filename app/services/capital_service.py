from app.core.normalize import validate_code
from app.providers.eastmoney import (
    fetch_fund_flow_minute,
    fetch_margin_trading,
    fetch_block_trade,
    fetch_holder_num,
    fetch_dividend_history,
    fetch_fund_flow_daily,
)


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


def get_block_trade(code: str) -> list[dict]:
    """Get block trade records for a stock."""
    code = validate_code(code)
    raw = fetch_block_trade(code)
    rows = []
    for row in raw:
        close = row.get("CLOSE_PRICE") or 0
        deal_price = row.get("DEAL_PRICE") or 0
        premium = ((deal_price / close - 1) * 100) if close else 0
        rows.append({
            "date": str(row.get("TRADE_DATE", ""))[:10],
            "price": deal_price,
            "close": close,
            "premium_pct": round(premium, 2),
            "vol": row.get("DEAL_VOLUME", 0),
            "amount": row.get("DEAL_AMT", 0),
            "buyer": row.get("BUYER_NAME", ""),
            "seller": row.get("SELLER_NAME", ""),
        })
    return rows


def get_holder_num(code: str) -> list[dict]:
    """Get shareholder count changes for a stock."""
    code = validate_code(code)
    raw = fetch_holder_num(code)
    rows = []
    for row in raw:
        rows.append({
            "date": str(row.get("END_DATE", ""))[:10],
            "holder_num": row.get("HOLDER_NUM", 0),
            "change_num": row.get("HOLDER_NUM_CHANGE", 0),
            "change_ratio": row.get("HOLDER_NUM_RATIO", 0),
            "avg_shares": row.get("AVG_FREE_SHARES", 0),
        })
    return rows


def get_dividend_history(code: str) -> list[dict]:
    """Get dividend/bonus history for a stock."""
    code = validate_code(code)
    raw = fetch_dividend_history(code)
    rows = []
    for row in raw:
        rows.append({
            "date": str(row.get("EX_DIVIDEND_DATE", ""))[:10],
            "bonus_rmb": row.get("PRETAX_BONUS_RMB", 0),
            "transfer_ratio": row.get("TRANSFER_RATIO", 0),
            "bonus_ratio": row.get("BONUS_RATIO", 0),
            "plan": row.get("ASSIGN_PROGRESS", ""),
        })
    return rows


def get_fund_flow_daily(code: str) -> list[dict]:
    """Get 120-day daily fund flow for a stock."""
    code = validate_code(code)
    return fetch_fund_flow_daily(code)

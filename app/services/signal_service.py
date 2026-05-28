"""Signal layer services: dragon tiger board, lockup expiry, industry ranking, concept blocks."""
from datetime import datetime, timedelta

from app.core.normalize import validate_code
from app.providers.baidu import fetch_concept_blocks
from app.providers.eastmoney import (
    fetch_billboard_records,
    fetch_billboard_seats,
    fetch_daily_billboard,
    fetch_lockup_expiry,
    fetch_industry_ranking,
)


def get_billboard(code: str, trade_date: str | None = None, look_back: int = 30) -> dict:
    """Get dragon tiger board data for a stock.

    Returns: {records: [...], seats: {buy: [...], sell: [...]}}
    """
    code = validate_code(code)
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=look_back)
    start_str = start.strftime("%Y-%m-%d")

    # 1. Records
    data = fetch_billboard_records(code, start_str, trade_date)
    records = []
    for row in data:
        records.append({
            "date": str(row.get("TRADE_DATE", ""))[:10],
            "reason": row.get("EXPLANATION", ""),
            "net_buy_wan": round((row.get("BILLBOARD_NET_AMT") or 0) / 10000, 1),
            "turnover_pct": round(float(row.get("TURNOVERRATE") or 0), 2),
        })

    # 2. Buy/sell seats for latest date
    seats = {"buy": [], "sell": []}
    if records:
        latest_date = records[0]["date"]
        for side in ("buy", "sell"):
            seat_data = fetch_billboard_seats(code, latest_date, side)
            for row in seat_data[:5]:
                seats[side].append({
                    "name": row.get("OPERATEDEPT_NAME", ""),
                    "buy_amt_wan": round((row.get("BUY") or 0) / 10000, 1),
                    "sell_amt_wan": round((row.get("SELL") or 0) / 10000, 1),
                    "net_wan": round((row.get("NET") or 0) / 10000, 1),
                })

    return {"records": records, "seats": seats}


def get_daily_billboard(trade_date: str | None = None) -> dict:
    """Get full market dragon tiger board for a date.

    Returns: {date, total_records, stocks: [...]}
    """
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y-%m-%d")

    data = fetch_daily_billboard(trade_date)
    if not data:
        return {"date": trade_date, "total_records": 0, "stocks": []}

    actual_date = str(data[0].get("TRADE_DATE", ""))[:10] if data else trade_date
    stocks = []
    for row in data:
        stocks.append({
            "code": row.get("SECURITY_CODE", ""),
            "name": row.get("SECURITY_NAME_ABBR", ""),
            "reason": row.get("EXPLANATION", ""),
            "close": row.get("CLOSE_PRICE") or 0,
            "change_pct": round(float(row.get("CHANGE_RATE") or 0), 2),
            "net_buy_wan": round((row.get("BILLBOARD_NET_AMT") or 0) / 10000, 1),
            "buy_wan": round((row.get("BILLBOARD_BUY_AMT") or 0) / 10000, 1),
            "sell_wan": round((row.get("BILLBOARD_SELL_AMT") or 0) / 10000, 1),
            "turnover_pct": round(float(row.get("TURNOVERRATE") or 0), 2),
        })
    return {"date": actual_date, "total_records": len(stocks), "stocks": stocks}


def get_lockup_expiry(code: str) -> list[dict]:
    """Get lockup expiry records for a stock."""
    code = validate_code(code)
    raw = fetch_lockup_expiry(code)
    rows = []
    for row in raw:
        rows.append({
            "date": str(row.get("FREE_DATE", ""))[:10],
            "type": row.get("LIMITED_STOCK_TYPE", ""),
            "shares": row.get("FREE_SHARES_NUM", 0),
            "ratio": row.get("FREE_RATIO", 0),
        })
    return rows


def get_industry_ranking(top_n: int = 20) -> dict:
    """Get industry sector ranking.

    Returns: {top: [...], bottom: [...], total: int}
    """
    items = fetch_industry_ranking()
    if not items:
        return {"top": [], "bottom": [], "total": 0}

    rows = []
    for i, item in enumerate(items):
        rows.append({
            "rank": i + 1,
            "name": item.get("f14", ""),
            "change_pct": item.get("f3", 0),
            "code": item.get("f12", ""),
            "up_count": item.get("f104", 0),
            "down_count": item.get("f105", 0),
            "leader": item.get("f140", ""),
            "leader_change": item.get("f136", 0),
        })

    return {
        "top": rows[:top_n],
        "bottom": rows[-top_n:],
        "total": len(rows),
    }


def get_concept_blocks(code: str) -> dict:
    """Get concept block classification for a stock from Baidu.

    Returns: {industry: [...], concept: [...], region: [...], concept_tags: [...]}
    """
    code = validate_code(code)
    return fetch_concept_blocks(code)

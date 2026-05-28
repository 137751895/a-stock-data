from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.signal_service import (
    get_billboard,
    get_daily_billboard,
    get_lockup_expiry,
    get_industry_ranking,
)

router = APIRouter()


@router.get("/billboard/daily")
def daily_billboard(trade_date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_daily_billboard(trade_date=trade_date)
    return success_response(data=data, source=["eastmoney"])


@router.get("/billboard/{code}")
def billboard(code: str, trade_date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_billboard(code, trade_date=trade_date)
    return success_response(data=data, source=["eastmoney"])


@router.get("/lockup/{code}")
def lockup(code: str):
    data = get_lockup_expiry(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/industry-ranking")
def industry_ranking(top_n: int = Query(20, description="Number of top/bottom sectors")):
    data = get_industry_ranking(top_n=top_n)
    return success_response(data=data, source=["eastmoney"])

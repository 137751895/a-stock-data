from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.signal_service import (
    get_billboard,
    get_concept_blocks,
    get_daily_billboard,
    get_hot_stocks,
    get_lockup_expiry,
    get_industry_ranking,
    get_northbound_realtime,
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


@router.get("/concept-blocks/{code}")
def concept_blocks(code: str):
    data = get_concept_blocks(code)
    return success_response(data=data, source=["baidu"])


@router.get("/hot-stocks")
def hot_stocks(date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_hot_stocks(date=date)
    return success_response(data=data, source=["ths"])


@router.get("/northbound")
def northbound():
    data = get_northbound_realtime()
    return success_response(data=data, source=["ths"])

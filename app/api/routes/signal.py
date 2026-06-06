from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse, success_response
from app.services.signal_service import (
    get_billboard,
    get_concept_blocks,
    get_daily_billboard,
    get_hot_stocks,
    get_lockup_expiry,
    get_industry_ranking,
    get_northbound_realtime,
    get_northbound_history,
)

router = APIRouter()


@router.get("/billboard/daily", response_model=ApiResponse)
def daily_billboard(trade_date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_daily_billboard(trade_date=trade_date)
    return success_response(data=data, source=["eastmoney"])


@router.get("/billboard/{code}", response_model=ApiResponse)
def billboard(code: str, trade_date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_billboard(code, trade_date=trade_date)
    return success_response(data=data, source=["eastmoney"])


@router.get("/lockup/{code}", response_model=ApiResponse)
def lockup(code: str):
    data = get_lockup_expiry(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/industry-ranking", response_model=ApiResponse)
def industry_ranking(top_n: int = Query(20, description="Number of top/bottom sectors")):
    data = get_industry_ranking(top_n=top_n)
    return success_response(data=data, source=["eastmoney"])


@router.get("/concept-blocks/{code}", response_model=ApiResponse)
def concept_blocks(code: str):
    data = get_concept_blocks(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/hot-stocks", response_model=ApiResponse)
def hot_stocks(date: str = Query(None, description="YYYY-MM-DD, defaults to today")):
    data = get_hot_stocks(date=date)
    return success_response(data=data, source=["ths"])


@router.get("/northbound", response_model=ApiResponse)
def northbound():
    data = get_northbound_realtime()
    return success_response(data=data, source=["ths"])


@router.get("/northbound/history", response_model=ApiResponse)
def northbound_history(days: int = Query(30, ge=1, le=365, description="Number of days")):
    data = get_northbound_history(days=days)
    return success_response(data=data, source=["ths"], cached=True)

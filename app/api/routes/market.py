from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse, success_response
from app.services.market_service import get_quotes, get_kline, get_mootdx_kline, get_mootdx_quotes, get_mootdx_transaction

router = APIRouter()


@router.get("/quote", response_model=ApiResponse)
def quote(codes: str = Query(..., description="Comma-separated stock codes, e.g. 600519,000858")):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return success_response(data={}, warnings=["No valid codes provided"])
    data = get_quotes(code_list)
    return success_response(data=data, source=["tencent"])


@router.get("/kline/{code}", response_model=ApiResponse)
def kline(code: str):
    data = get_kline(code)
    return success_response(data=data, source=["baidu"])


@router.get("/mootdx-kline/{code}", response_model=ApiResponse)
def mootdx_kline(
    code: str,
    category: str = Query("daily", description="K-line period: daily/weekly/monthly/1min/5min/15min/30min/60min"),
    offset: int = Query(100, description="Number of bars to return", ge=1, le=800),
):
    data = get_mootdx_kline(code, category=category, offset=offset)
    return success_response(data=data, source=["mootdx"])


@router.get("/mootdx-quotes", response_model=ApiResponse)
def mootdx_quotes(
    codes: str = Query(..., description="Comma-separated stock codes, e.g. 688017,300476"),
):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return success_response(data=[], warnings=["No valid codes provided"])
    data = get_mootdx_quotes(code_list)
    return success_response(data=data, source=["mootdx"])


@router.get("/mootdx-transaction/{code}", response_model=ApiResponse)
def mootdx_transaction(
    code: str,
    date: str = Query("", description="Date in YYYYMMDD format. Empty = today"),
):
    data = get_mootdx_transaction(code, date=date)
    return success_response(data=data, source=["mootdx"])

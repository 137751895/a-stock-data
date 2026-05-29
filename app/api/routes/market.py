from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse, success_response
from app.services.market_service import get_quotes, get_kline

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

from fastapi import APIRouter

from app.schemas.common import ApiResponse, success_response
from app.services.capital_service import (
    get_fund_flow_minute,
    get_margin_trading,
    get_block_trade,
    get_holder_num,
    get_dividend_history,
    get_fund_flow_daily,
)

router = APIRouter()


@router.get("/fund-flow/minute/{code}", response_model=ApiResponse)
def fund_flow_minute(code: str):
    data = get_fund_flow_minute(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/margin/{code}", response_model=ApiResponse)
def margin(code: str):
    data = get_margin_trading(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/block-trade/{code}", response_model=ApiResponse)
def block_trade(code: str):
    data = get_block_trade(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/holder-num/{code}", response_model=ApiResponse)
def holder_num(code: str):
    data = get_holder_num(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/dividend/{code}", response_model=ApiResponse)
def dividend(code: str):
    data = get_dividend_history(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/fund-flow/daily/{code}", response_model=ApiResponse)
def fund_flow_daily(code: str):
    data = get_fund_flow_daily(code)
    return success_response(data=data, source=["eastmoney"])

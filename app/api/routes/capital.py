from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.capital_service import get_fund_flow_minute, get_margin_trading

router = APIRouter()


@router.get("/fund-flow/minute/{code}")
def fund_flow_minute(code: str):
    data = get_fund_flow_minute(code)
    return success_response(data=data, source=["eastmoney"])


@router.get("/margin/{code}")
def margin(code: str):
    data = get_margin_trading(code)
    return success_response(data=data, source=["eastmoney"])

from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.fundamentals_service import get_stock_info, get_financial_report

router = APIRouter()


@router.get("/stock-info/{code}")
def stock_info(code: str):
    data, cached = get_stock_info(code)
    return success_response(data=data, source=["eastmoney"], cached=cached)


@router.get("/financial-report/{code}")
def financial_report(code: str, report_type: str = Query("lrb", description="fzb/lrb/llb")):
    data = get_financial_report(code, report_type)
    return success_response(data=data, source=["sina"])

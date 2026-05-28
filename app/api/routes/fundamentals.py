from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.fundamentals_service import (
    get_stock_info,
    get_financial_report,
    get_finance_snapshot,
    get_f10,
    get_f10_announcement,
)

router = APIRouter()


@router.get("/stock-info/{code}")
def stock_info(code: str):
    data, cached = get_stock_info(code)
    return success_response(data=data, source=["eastmoney"], cached=cached)


@router.get("/financial-report/{code}")
def financial_report(code: str, report_type: str = Query("lrb", description="fzb/lrb/llb")):
    data = get_financial_report(code, report_type)
    return success_response(data=data, source=["sina"])


@router.get("/finance-snapshot/{code}")
def finance_snapshot(code: str):
    data = get_finance_snapshot(code)
    return success_response(data=data, source=["mootdx"])


@router.get("/f10/{code}")
def f10(code: str, category: str = Query("公司概况", description="F10 category name")):
    data = get_f10(code, category)
    return success_response(data=data, source=["mootdx"])


@router.get("/f10-announcement/{code}")
def f10_announcement(code: str):
    data = get_f10_announcement(code)
    return success_response(data=data, source=["mootdx"])

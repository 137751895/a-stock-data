from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse, success_response
from app.services.fundamentals_service import (
    get_stock_info,
    get_financial_report,
    get_finance_snapshot,
    get_f10,
    get_f10_announcement,
)

router = APIRouter()


@router.get("/stock-info/{code}", response_model=ApiResponse)
def stock_info(code: str):
    data, cached = get_stock_info(code)
    return success_response(data=data, source=["eastmoney"], cached=cached)


@router.get("/financial-report/{code}", response_model=ApiResponse)
def financial_report(
    code: str,
    report_type: str = Query("lrb", description="fzb/lrb/llb"),
    num: int = Query(8, ge=1, le=60, description="Number of most recent reporting periods"),
):
    data = get_financial_report(code, report_type, num)
    return success_response(data=data, source=["sina"])


@router.get("/finance-snapshot/{code}", response_model=ApiResponse)
def finance_snapshot(code: str):
    data = get_finance_snapshot(code)
    return success_response(data=data, source=["mootdx"])


@router.get("/f10/{code}", response_model=ApiResponse)
def f10(code: str, category: str = Query("公司概况", description="F10 category name")):
    data = get_f10(code, category)
    return success_response(data=data, source=["mootdx"])


@router.get("/f10-announcement/{code}", response_model=ApiResponse)
def f10_announcement(code: str):
    data = get_f10_announcement(code)
    return success_response(data=data, source=["mootdx"])

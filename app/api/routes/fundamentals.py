from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.fundamentals_service import get_stock_info

router = APIRouter()


@router.get("/stock-info/{code}")
def stock_info(code: str):
    data, cached = get_stock_info(code)
    return success_response(data=data, source=["eastmoney"], cached=cached)

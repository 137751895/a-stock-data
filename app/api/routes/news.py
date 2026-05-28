from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.news_service import get_stock_news

router = APIRouter()


@router.get("/news/{code}")
def news(code: str):
    data = get_stock_news(code)
    return success_response(data=data, source=["eastmoney"])

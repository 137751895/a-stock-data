from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.news_service import get_stock_news, get_cls_telegraph, get_global_news

router = APIRouter()


@router.get("/telegraph")
def telegraph():
    data = get_cls_telegraph()
    return success_response(data=data, source=["cls"])


@router.get("/global-news")
def global_news():
    data = get_global_news()
    return success_response(data=data, source=["eastmoney"])


@router.get("/news/{code}")
def news(code: str):
    data = get_stock_news(code)
    return success_response(data=data, source=["eastmoney"])

from fastapi import APIRouter

from app.schemas.common import ApiResponse, success_response
from app.services.news_service import get_stock_news, get_cls_telegraph, get_global_news

router = APIRouter()


@router.get("/telegraph", response_model=ApiResponse)
def telegraph():
    data = get_cls_telegraph()
    return success_response(data=data, source=["cls"])


@router.get("/global-news", response_model=ApiResponse)
def global_news():
    data = get_global_news()
    return success_response(data=data, source=["eastmoney"])


@router.get("/news/{code}", response_model=ApiResponse)
def news(code: str):
    data = get_stock_news(code)
    return success_response(data=data, source=["eastmoney"])

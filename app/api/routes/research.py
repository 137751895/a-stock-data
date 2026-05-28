from fastapi import APIRouter, Query

from app.schemas.common import success_response
from app.services.research_service import get_reports, get_iwencai_search

router = APIRouter()


@router.get("/reports/{code}")
def reports(code: str):
    data, cached = get_reports(code)
    return success_response(data=data, source=["eastmoney"], cached=cached)


@router.get("/iwencai-search")
def iwencai_search(
    query: str = Query(..., description="NL search query"),
    channel: str = Query("report", description="report/announcement/news"),
    size: int = Query(50, ge=1, le=100, description="Number of results"),
):
    data = get_iwencai_search(query, channel=channel, size=size)
    return success_response(data=data, source=["iwencai"])

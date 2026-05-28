from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.research_service import get_reports

router = APIRouter()


@router.get("/reports/{code}")
def reports(code: str):
    data = get_reports(code)
    return success_response(data=data, source=["eastmoney"])

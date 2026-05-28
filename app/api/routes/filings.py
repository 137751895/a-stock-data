from fastapi import APIRouter

from app.schemas.common import success_response
from app.services.filings_service import get_announcements

router = APIRouter()


@router.get("/announcements/{code}")
async def announcements(code: str):
    data = get_announcements(code)
    return success_response(data=data, source=["cninfo"])

from fastapi import APIRouter

from app.schemas.common import success_response

router = APIRouter()


@router.get("/health")
async def health_check():
    return success_response(data={"status": "ok"}, source=["self"])

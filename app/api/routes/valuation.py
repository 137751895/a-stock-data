from fastapi import APIRouter

from app.schemas.common import ApiResponse, success_response
from app.services.valuation_service import get_valuation

router = APIRouter()


@router.get("/valuation/{code}", response_model=ApiResponse)
def valuation(code: str):
    result = get_valuation(code)
    return success_response(
        data=result["data"],
        source=result["source"],
        warnings=result["warnings"],
    )

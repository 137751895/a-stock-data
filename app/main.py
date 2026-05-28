from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.market import router as market_router
from app.api.routes.fundamentals import router as fundamentals_router
from app.core.errors import AppError, app_error_handler

app = FastAPI(title="a-stock-data API", version="4.0.0")

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(fundamentals_router, prefix="/api/v1")

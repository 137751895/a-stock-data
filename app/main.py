from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.market import router as market_router
from app.api.routes.fundamentals import router as fundamentals_router
from app.api.routes.valuation import router as valuation_router
from app.api.routes.research import router as research_router
from app.api.routes.capital import router as capital_router
from app.api.routes.news import router as news_router
from app.api.routes.filings import router as filings_router
from app.core.errors import AppError, app_error_handler

app = FastAPI(title="a-stock-data API", version="4.0.0")

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(fundamentals_router, prefix="/api/v1")
app.include_router(valuation_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(capital_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(filings_router, prefix="/api/v1")

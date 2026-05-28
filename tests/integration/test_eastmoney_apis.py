from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_REPORTS = [{"title": "Test Report", "publishDate": "2026-05-28"}]
MOCK_FUND_FLOW = [{"time": "09:30", "main_net": 100.0}]
MOCK_MARGIN = [{"TRADE_DATE": "2026-05-28", "RZYE": 1000000}]
MOCK_NEWS = [{"title": "Test News", "time": "2026-05-28", "source": "Source", "url": "http://test.com", "content": "..."}]


@patch("app.services.research_service.fetch_reports", return_value=MOCK_REPORTS)
def test_reports_api(mock_fetch):
    response = client.get("/api/v1/reports/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["source"] == ["eastmoney"]


@patch("app.services.capital_service.fetch_fund_flow_minute", return_value=MOCK_FUND_FLOW)
def test_fund_flow_minute_api(mock_fetch):
    response = client.get("/api/v1/fund-flow/minute/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["source"] == ["eastmoney"]


@patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_MARGIN)
def test_margin_api(mock_fetch):
    response = client.get("/api/v1/margin/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("app.services.news_service.fetch_stock_news", return_value=MOCK_NEWS)
def test_news_api(mock_fetch):
    response = client.get("/api/v1/news/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1

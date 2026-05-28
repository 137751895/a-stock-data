from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_INFO = {
    "code": "600519",
    "name": "贵州茅台",
    "industry": "白酒",
    "total_shares": 1256198000,
    "float_shares": 1256198000,
    "mcap": 2260000000000,
    "float_mcap": 2260000000000,
    "list_date": "20010827",
    "price": 1800.0,
}


@patch("app.services.fundamentals_service.fetch_stock_info", return_value=MOCK_INFO)
def test_stock_info_returns_200(mock_fetch):
    response = client.get("/api/v1/stock-info/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["code"] == "600519"
    assert data["data"]["name"] == "贵州茅台"
    assert data["source"] == ["eastmoney"]


@patch("app.services.fundamentals_service.fetch_stock_info", return_value=MOCK_INFO)
def test_stock_info_returns_envelope(mock_fetch):
    response = client.get("/api/v1/stock-info/600519")
    data = response.json()
    assert "request_id" in data
    assert isinstance(data["warnings"], list)

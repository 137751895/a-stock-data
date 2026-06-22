from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_quotes(codes):
    return {c: {"name": f"Stock_{c}", "price": 100.0, "pe_ttm": 30.0, "pb": 5.0,
                "amplitude_pct": 3.0, "mcap_yi": 1000.0} for c in codes}


@patch("app.services.market_service.fetch_quotes", side_effect=_mock_quotes)
def test_quote_returns_200(mock_fetch):
    response = client.get("/api/v1/quote?codes=600519,000858")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "600519" in data["data"]
    assert "000858" in data["data"]
    assert data["source"] == ["tencent"]


@patch("app.services.market_service.fetch_quotes", side_effect=_mock_quotes)
def test_quote_returns_envelope(mock_fetch):
    response = client.get("/api/v1/quote?codes=600519")
    data = response.json()
    assert "request_id" in data
    assert "fetched_at" in data
    assert isinstance(data["warnings"], list)

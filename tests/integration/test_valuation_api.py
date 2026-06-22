from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_QUOTES = {
    "600519": {
        "name": "贵州茅台", "price": 1800.0, "mcap_yi": 22600.0,
        "pe_ttm": 30.0, "pb": 11.0, "amplitude_pct": 3.0,
    }
}

MOCK_THS = {"html": ""}


@patch("app.services.valuation_service.fetch_quotes", return_value=MOCK_QUOTES)
@patch("app.services.valuation_service.fetch_eps_forecast", return_value=MOCK_THS)
@patch("app.services.valuation_service.parse_ths_eps_table")
@patch("app.services.valuation_service.extract_eps_from_df", return_value={
    "eps_cur": 60.0, "eps_next": 78.0, "analyst_count": 25,
})
def test_valuation_returns_200(mock_eps, mock_parse, mock_ths, mock_quotes):
    response = client.get("/api/v1/valuation/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["code"] == "600519"
    assert data["data"]["pe_fwd"] is not None
    assert data["data"]["peg"] is not None


@patch("app.services.valuation_service.fetch_quotes", return_value=MOCK_QUOTES)
@patch("app.services.valuation_service.fetch_eps_forecast",
       side_effect=ConnectionError("THS down"))
def test_valuation_partial_failure_returns_warnings(mock_ths, mock_quotes):
    """When THS fails with a degradable error, valuation should still return with warnings."""
    response = client.get("/api/v1/valuation/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["warnings"]) > 0
    assert data["data"]["eps_cur"] is None


@patch("app.services.valuation_service.fetch_quotes", return_value=MOCK_QUOTES)
@patch("app.services.valuation_service.fetch_eps_forecast", return_value=MOCK_THS)
@patch("app.services.valuation_service.parse_ths_eps_table")
@patch("app.services.valuation_service.extract_eps_from_df", return_value={
    "eps_cur": None, "eps_next": None, "analyst_count": 0,
})
def test_valuation_with_no_eps_returns_warnings(mock_eps, mock_parse, mock_ths, mock_quotes):
    response = client.get("/api/v1/valuation/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["pe_fwd"] is None
    assert any("EPS" in w for w in data["warnings"])


@patch("app.services.valuation_service.fetch_quotes", return_value=MOCK_QUOTES)
@patch("app.services.valuation_service.fetch_eps_forecast", return_value=MOCK_THS)
@patch("app.services.valuation_service.parse_ths_eps_table")
@patch("app.services.valuation_service.extract_eps_from_df", return_value={
    "eps_cur": 60.0, "eps_next": 60.0, "analyst_count": 25,
})
def test_valuation_zero_cagr_returns_null_peg(mock_eps, mock_parse, mock_ths, mock_quotes):
    """When eps_next == eps_cur, cagr=0, PEG and digest_years should be None."""
    response = client.get("/api/v1/valuation/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["cagr_pct"] is None  # cagr=0 → falsy → None
    assert data["data"]["peg"] is None
    assert data["data"]["digest_years"] is None


@patch("app.services.valuation_service.fetch_quotes", return_value=MOCK_QUOTES)
@patch("app.services.valuation_service.fetch_eps_forecast", return_value=MOCK_THS)
@patch("app.services.valuation_service.parse_ths_eps_table")
@patch("app.services.valuation_service.extract_eps_from_df", return_value={
    "eps_cur": 60.0, "eps_next": 30.0, "analyst_count": 25,
})
def test_valuation_negative_cagr_returns_null_peg(mock_eps, mock_parse, mock_ths, mock_quotes):
    """When eps declines, cagr < 0, PEG should be None."""
    response = client.get("/api/v1/valuation/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["peg"] is None
    assert data["data"]["digest_years"] is None

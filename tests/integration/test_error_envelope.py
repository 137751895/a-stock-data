"""Integration tests for unified error envelope.

Tests that AppError subclasses are properly caught and returned
as the unified envelope matching success_response structure.

Error responses MUST contain the same top-level keys as success responses:
success, request_id, data, source, cached, warnings, fetched_at, error
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.errors import UpstreamHTTPError, UpstreamSchemaError
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

ENVELOPE_KEYS = {"success", "request_id", "data", "source", "cached", "warnings", "fetched_at", "error"}


def _assert_error_envelope(data: dict, expected_code: str, expected_provider: str | None = None):
    """Verify error response contains all unified envelope fields."""
    assert set(data.keys()) == ENVELOPE_KEYS, f"Missing keys: {ENVELOPE_KEYS - set(data.keys())}"
    assert data["success"] is False
    assert isinstance(data["request_id"], str) and len(data["request_id"]) > 0
    assert data["data"] is None
    assert data["source"] == []
    assert data["cached"] is False
    assert isinstance(data["warnings"], list)
    assert isinstance(data["fetched_at"], str) and len(data["fetched_at"]) > 0
    assert data["error"]["code"] == expected_code
    if expected_provider:
        assert data["error"]["provider"] == expected_provider


class TestErrorEnvelopeIntegration:
    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("Connection timeout", provider="eastmoney"))
    def test_upstream_error_returns_502_envelope(self, mock_fetch):
        response = client.get("/api/v1/stock-info/600519")
        assert response.status_code == 502
        _assert_error_envelope(response.json(), "UPSTREAM_HTTP_ERROR", "eastmoney")

    @patch("app.services.research_service.fetch_reports",
           side_effect=UpstreamSchemaError("JSON parse failed", provider="eastmoney"))
    def test_schema_error_returns_502_envelope(self, mock_fetch):
        response = client.get("/api/v1/reports/600519")
        assert response.status_code == 502
        _assert_error_envelope(response.json(), "UPSTREAM_SCHEMA_ERROR", "eastmoney")

    def test_invalid_code_returns_400_envelope(self):
        response = client.get("/api/v1/stock-info/INVALID")
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "VALIDATION_ERROR")

    def test_invalid_code_in_news_returns_400(self):
        response = client.get("/api/v1/news/ABC")
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "VALIDATION_ERROR")

    def test_invalid_code_in_margin_returns_400(self):
        response = client.get("/api/v1/margin/XYZ")
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "VALIDATION_ERROR")

    def test_invalid_code_in_reports_returns_400(self):
        response = client.get("/api/v1/reports/12345")
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "VALIDATION_ERROR")

    def test_invalid_code_in_announcements_returns_400(self):
        response = client.get("/api/v1/announcements/bad_code")
        assert response.status_code == 400
        _assert_error_envelope(response.json(), "VALIDATION_ERROR")

    @patch("app.services.capital_service.fetch_fund_flow_minute",
           side_effect=UpstreamHTTPError("503 from upstream", provider="eastmoney"))
    def test_fund_flow_upstream_error_returns_envelope(self, mock_fetch):
        response = client.get("/api/v1/fund-flow/minute/600519")
        assert response.status_code == 502
        _assert_error_envelope(response.json(), "UPSTREAM_HTTP_ERROR", "eastmoney")


class TestErrorEnvelopeFieldCompleteness:
    """Verify error envelope has ALL the same top-level fields as success envelope."""

    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("timeout", provider="eastmoney"))
    def test_error_has_request_id(self, mock_fetch):
        data = client.get("/api/v1/stock-info/600519").json()
        assert "request_id" in data
        assert len(data["request_id"]) == 36  # UUID format

    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("timeout", provider="eastmoney"))
    def test_error_has_fetched_at(self, mock_fetch):
        data = client.get("/api/v1/stock-info/600519").json()
        assert "fetched_at" in data
        assert "T" in data["fetched_at"]  # ISO format

    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("timeout", provider="eastmoney"))
    def test_error_has_data_null(self, mock_fetch):
        data = client.get("/api/v1/stock-info/600519").json()
        assert data["data"] is None

    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("timeout", provider="eastmoney"))
    def test_error_has_source_empty(self, mock_fetch):
        data = client.get("/api/v1/stock-info/600519").json()
        assert data["source"] == []

    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("timeout", provider="eastmoney"))
    def test_error_has_cached_false(self, mock_fetch):
        data = client.get("/api/v1/stock-info/600519").json()
        assert data["cached"] is False

    def test_validation_error_has_full_envelope(self):
        data = client.get("/api/v1/stock-info/INVALID").json()
        _assert_error_envelope(data, "VALIDATION_ERROR")

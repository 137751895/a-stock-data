"""Integration tests for unified error envelope.

Tests that AppError subclasses are properly caught and returned
as the unified {success: false, error: {code, message, provider}} envelope.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.errors import UpstreamHTTPError, UpstreamSchemaError
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestErrorEnvelopeIntegration:
    @patch("app.services.fundamentals_service.fetch_stock_info",
           side_effect=UpstreamHTTPError("Connection timeout", provider="eastmoney"))
    def test_upstream_error_returns_502_envelope(self, mock_fetch):
        response = client.get("/api/v1/stock-info/600519")
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UPSTREAM_HTTP_ERROR"
        assert data["error"]["provider"] == "eastmoney"
        assert isinstance(data["warnings"], list)

    @patch("app.services.research_service.fetch_reports",
           side_effect=UpstreamSchemaError("JSON parse failed", provider="eastmoney"))
    def test_schema_error_returns_502_envelope(self, mock_fetch):
        response = client.get("/api/v1/reports/600519")
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "UPSTREAM_SCHEMA_ERROR"

    def test_invalid_code_returns_400_envelope(self):
        response = client.get("/api/v1/stock-info/INVALID")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_invalid_code_in_news_returns_400(self):
        response = client.get("/api/v1/news/ABC")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    def test_invalid_code_in_margin_returns_400(self):
        response = client.get("/api/v1/margin/XYZ")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_invalid_code_in_reports_returns_400(self):
        response = client.get("/api/v1/reports/12345")
        assert response.status_code == 400

    def test_invalid_code_in_announcements_returns_400(self):
        response = client.get("/api/v1/announcements/bad_code")
        assert response.status_code == 400

    @patch("app.services.capital_service.fetch_fund_flow_minute",
           side_effect=UpstreamHTTPError("503 from upstream", provider="eastmoney"))
    def test_fund_flow_upstream_error_returns_envelope(self, mock_fetch):
        response = client.get("/api/v1/fund-flow/minute/600519")
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"]["provider"] == "eastmoney"

"""Integration tests for iwencai search API endpoint."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.errors import ProviderAuthError
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


MOCK_SEARCH_RESULTS = [
    {"uid": "1", "title": "Report A", "publish_date": "2026-05-28", "score": 0.9},
    {"uid": "2", "title": "Report B", "publish_date": "2026-05-27", "score": 0.8},
]


class TestIwencaiSearchAPI:
    @patch("app.providers.iwencai.fetch_iwencai_search", return_value=MOCK_SEARCH_RESULTS)
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/iwencai-search?query=人形机器人")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["iwencai"]
        assert len(data["data"]) == 2

    @patch("app.providers.iwencai.fetch_iwencai_search",
           side_effect=ProviderAuthError("IWENCAI_API_KEY not configured", provider="iwencai"))
    def test_returns_403_without_key(self, mock_fetch):
        response = client.get("/api/v1/iwencai-search?query=test")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PROVIDER_AUTH_ERROR"

    def test_returns_422_without_query(self):
        response = client.get("/api/v1/iwencai-search")
        assert response.status_code == 422

    def test_returns_400_with_empty_query(self):
        response = client.get("/api/v1/iwencai-search?query=  ")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_returns_400_with_invalid_channel(self):
        response = client.get("/api/v1/iwencai-search?query=test&channel=invalid")
        assert response.status_code == 400

    @patch("app.providers.iwencai.fetch_iwencai_search", return_value=[])
    def test_returns_empty_results(self, mock_fetch):
        response = client.get("/api/v1/iwencai-search?query=test&channel=news")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

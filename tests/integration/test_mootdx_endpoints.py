"""Integration tests for mootdx-based endpoints (finance-snapshot, f10, f10-announcement).

All tests mock the mootdx provider since TCP is unavailable in CI.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.providers.mootdx_provider import DependencyUnavailableError

client = TestClient(app, raise_server_exceptions=False)


class TestFinanceSnapshotAPI:
    @patch("app.providers.mootdx_provider.fetch_finance_snapshot",
           return_value=[{"eps": 1.5, "bvps": 10.2, "roe": 15.0}])
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/finance-snapshot/688017")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["mootdx"]
        assert len(data["data"]) == 1
        assert data["data"][0]["eps"] == 1.5

    @patch("app.providers.mootdx_provider.fetch_finance_snapshot",
           side_effect=DependencyUnavailableError("mootdx is not installed"))
    def test_returns_503_when_unavailable(self, mock_fetch):
        response = client.get("/api/v1/finance-snapshot/688017")
        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DEPENDENCY_UNAVAILABLE"

    def test_invalid_code(self):
        response = client.get("/api/v1/finance-snapshot/ABC")
        assert response.status_code == 400


class TestF10API:
    @patch("app.providers.mootdx_provider.fetch_f10",
           return_value="公司简介：xxx")
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/f10/688017?category=公司概况")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["category"] == "公司概况"
        assert data["data"]["content"] == "公司简介：xxx"

    @patch("app.providers.mootdx_provider.fetch_f10",
           side_effect=DependencyUnavailableError("mootdx is not installed"))
    def test_returns_503_when_unavailable(self, mock_fetch):
        response = client.get("/api/v1/f10/688017")
        assert response.status_code == 503

    def test_invalid_category(self):
        response = client.get("/api/v1/f10/688017?category=invalid")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestF10AnnouncementAPI:
    @patch("app.providers.mootdx_provider.fetch_f10_announcement",
           return_value="最新公告内容")
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/f10-announcement/688017")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["category"] == "最新提示"
        assert data["data"]["content"] == "最新公告内容"

    @patch("app.providers.mootdx_provider.fetch_f10_announcement",
           side_effect=DependencyUnavailableError("TCP connection failed"))
    def test_returns_503_when_unavailable(self, mock_fetch):
        response = client.get("/api/v1/f10-announcement/688017")
        assert response.status_code == 503

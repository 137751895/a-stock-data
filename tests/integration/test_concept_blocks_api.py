"""Integration tests for concept blocks API endpoint (Eastmoney slist, V3.2.2)."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


MOCK_CONCEPT_RESULT = {
    "total": 3,
    "boards": [
        {"name": "食品饮料", "code": "BK0438", "change_pct": "2.15", "lead_stock": "贵州茅台"},
        {"name": "白酒", "code": "BK0477", "change_pct": "3.20", "lead_stock": "贵州茅台"},
        {"name": "贵州板块", "code": "BK0153", "change_pct": "0.80", "lead_stock": "贵州茅台"},
    ],
    "concept_tags": ["食品饮料", "白酒", "贵州板块"],
}


class TestConceptBlocksAPI:
    @patch("app.services.signal_service.fetch_concept_blocks", return_value=MOCK_CONCEPT_RESULT)
    def test_concept_blocks_returns_200(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["eastmoney"]
        assert data["data"]["total"] == 3
        assert len(data["data"]["boards"]) == 3
        assert "白酒" in data["data"]["concept_tags"]

    @patch("app.services.signal_service.fetch_concept_blocks", return_value=MOCK_CONCEPT_RESULT)
    def test_concept_blocks_with_prefix(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/SH600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_fetch.assert_called_once_with("600519")

    def test_concept_blocks_invalid_code(self):
        response = client.get("/api/v1/concept-blocks/ABC")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("app.services.signal_service.fetch_concept_blocks", return_value={
        "total": 0, "boards": [], "concept_tags": []
    })
    def test_concept_blocks_empty_result(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["concept_tags"] == []

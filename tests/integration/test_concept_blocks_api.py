"""Integration tests for concept blocks API endpoint."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


MOCK_CONCEPT_RESULT = {
    "industry": [
        {"name": "半导体", "change_pct": "2.15", "desc": "申万二级"},
    ],
    "concept": [
        {"name": "芯片", "change_pct": "3.20", "desc": ""},
        {"name": "国产替代", "change_pct": "1.50", "desc": ""},
    ],
    "region": [
        {"name": "上海", "change_pct": "0.80", "desc": ""},
    ],
    "concept_tags": ["芯片", "国产替代"],
}


class TestConceptBlocksAPI:
    @patch("app.services.signal_service.fetch_concept_blocks", return_value=MOCK_CONCEPT_RESULT)
    def test_concept_blocks_returns_200(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/688017")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["baidu"]
        assert len(data["data"]["industry"]) == 1
        assert len(data["data"]["concept"]) == 2
        assert "芯片" in data["data"]["concept_tags"]

    @patch("app.services.signal_service.fetch_concept_blocks", return_value=MOCK_CONCEPT_RESULT)
    def test_concept_blocks_with_prefix(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/SH688017")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_fetch.assert_called_once_with("688017")

    def test_concept_blocks_invalid_code(self):
        response = client.get("/api/v1/concept-blocks/ABC")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @patch("app.services.signal_service.fetch_concept_blocks", return_value={
        "industry": [], "concept": [], "region": [], "concept_tags": []
    })
    def test_concept_blocks_empty_result(self, mock_fetch):
        response = client.get("/api/v1/concept-blocks/688017")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["concept_tags"] == []

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MOCK_ANNOUNCEMENTS = [
    {"title": "Test Ann", "type": "公告", "date": "2026-05-28", "url": "http://test.com"}
]


@patch("app.services.filings_service.fetch_announcements", return_value=MOCK_ANNOUNCEMENTS)
def test_announcements_api(mock_fetch):
    response = client.get("/api/v1/announcements/600519")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["source"] == ["cninfo"]

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_success_envelope():
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "request_id" in data
    assert "fetched_at" in data
    assert isinstance(data["warnings"], list)

"""Integration tests for THS hot stocks and northbound capital API endpoints.

These APIs depend on THS servers which may be blocked in CI/sandbox.
All tests use mocks for reliable CI execution.
"""
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


MOCK_HOT_STOCKS_RAW = [
    {
        "code": "600519", "name": "贵州茅台", "reason": "白酒+消费复苏",
        "close": "1800.00", "zhangfu": "5.20", "huanshou": "1.30",
        "chengjiaoe": "5000000000", "ddejingliang": "200000", "market": "沪",
    },
    {
        "code": "000858", "name": "五粮液", "reason": "白酒",
        "close": "180.00", "zhangfu": "3.10", "huanshou": "2.10",
        "chengjiaoe": "3000000000", "ddejingliang": "100000", "market": "深",
    },
]

MOCK_NORTHBOUND_RAW = {
    "time": ["09:30", "09:31", "09:32"],
    "hgt": [1.2, 1.5, 1.8],
    "sgt": [0.8, 0.9, 1.1],
}


class TestHotStocksAPI:
    @patch("app.services.signal_service.fetch_hot_stocks", return_value=MOCK_HOT_STOCKS_RAW)
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/hot-stocks?date=2026-05-27")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["ths"]
        assert data["data"]["total"] == 2
        assert data["data"]["stocks"][0]["code"] == "600519"
        assert data["data"]["stocks"][0]["reason"] == "白酒+消费复苏"

    @patch("app.services.signal_service.fetch_hot_stocks", return_value=[])
    def test_empty_result(self, mock_fetch):
        response = client.get("/api/v1/hot-stocks?date=2026-05-27")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["stocks"] == []

    @patch("app.services.signal_service.fetch_hot_stocks", return_value=MOCK_HOT_STOCKS_RAW)
    def test_defaults_to_today(self, mock_fetch):
        response = client.get("/api/v1/hot-stocks")
        assert response.status_code == 200
        # Should call with today's date
        mock_fetch.assert_called_once()


class TestNorthboundAPI:
    @patch("app.services.signal_service.fetch_northbound_realtime", return_value=MOCK_NORTHBOUND_RAW)
    def test_returns_200(self, mock_fetch):
        response = client.get("/api/v1/northbound")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["source"] == ["ths"]
        assert data["data"]["points"] == 3
        assert data["data"]["data"][0]["time"] == "09:30"
        assert data["data"]["data"][0]["hgt_yi"] == 1.2

    @patch("app.services.signal_service.fetch_northbound_realtime",
           return_value={"time": [], "hgt": [], "sgt": []})
    def test_empty_result(self, mock_fetch):
        response = client.get("/api/v1/northbound")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["points"] == 0


class TestNorthboundHistoryAPI:
    def test_returns_200_empty_when_no_cache(self):
        with patch("app.core.config.settings.cache_dir", ""):
            response = client.get("/api/v1/northbound/history")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total"] == 0

    def test_returns_cached_history(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                # Pre-populate history files
                history_dir = Path(tmpdir) / "northbound_history"
                history_dir.mkdir()
                for i, date in enumerate(["2026-05-27", "2026-05-28"]):
                    with open(history_dir / f"{date}.json", "w") as f:
                        json.dump({"date": date, "hgt_yi": 1.0 + i, "sgt_yi": 0.5 + i, "points": 100}, f)

                response = client.get("/api/v1/northbound/history?days=10")
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["total"] == 2
                assert data["data"]["data"][0]["date"] == "2026-05-28"  # sorted desc

    @patch("app.services.signal_service.fetch_northbound_realtime", return_value=MOCK_NORTHBOUND_RAW)
    def test_realtime_caches_daily_summary(self, mock_fetch):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                # Call realtime — should cache summary
                response = client.get("/api/v1/northbound")
                assert response.status_code == 200
                # Verify cache file was written
                history_dir = Path(tmpdir) / "northbound_history"
                files = list(history_dir.glob("*.json"))
                assert len(files) == 1

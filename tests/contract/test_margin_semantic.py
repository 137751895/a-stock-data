"""Contract tests for margin data semantic fields per SKILL.md.

Verifies that margin API returns normalized fields:
date, rzye, rzmre, rzche, rqye, rqmcl, rqchl, rzrqye
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.capital_service import get_margin_trading

client = TestClient(app)

# Mock raw datacenter response (uppercase Eastmoney keys)
MOCK_RAW_MARGIN = [
    {
        "DATE": "2026-05-28 00:00:00",
        "TRADE_DATE": "2026-05-28 00:00:00",
        "SECURITY_CODE": "600519",
        "MARKET": "上交所",
        "RZYE": 10000000000,
        "RZMRE": 500000000,
        "RZCHE": 480000000,
        "RQYE": 200000000,
        "RQMCL": 10000,
        "RQCHL": 9500,
        "RZRQYE": 10200000000,
    }
]


class TestMarginSemanticFields:
    @patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_RAW_MARGIN)
    def test_margin_returns_normalized_fields(self, mock_fetch):
        result = get_margin_trading("600519")
        assert len(result) == 1
        row = result[0]
        # SKILL.md semantic fields
        assert "date" in row
        assert "rzye" in row
        assert "rzmre" in row
        assert "rzche" in row
        assert "rqye" in row
        assert "rqmcl" in row
        assert "rqchl" in row
        assert "rzrqye" in row

    @patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_RAW_MARGIN)
    def test_margin_date_is_truncated_to_10_chars(self, mock_fetch):
        result = get_margin_trading("600519")
        assert result[0]["date"] == "2026-05-28"

    @patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_RAW_MARGIN)
    def test_margin_values_are_numeric(self, mock_fetch):
        result = get_margin_trading("600519")
        row = result[0]
        assert isinstance(row["rzye"], (int, float))
        assert row["rzye"] == 10000000000
        assert row["rzmre"] == 500000000
        assert row["rzrqye"] == 10200000000

    @patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_RAW_MARGIN)
    def test_margin_no_raw_uppercase_keys(self, mock_fetch):
        """Ensure raw Eastmoney keys are NOT leaked to the API."""
        result = get_margin_trading("600519")
        row = result[0]
        assert "TRADE_DATE" not in row
        assert "RZYE" not in row
        assert "MARKET" not in row
        assert "SECURITY_CODE" not in row

    @patch("app.services.capital_service.fetch_margin_trading", return_value=[])
    def test_margin_empty_returns_empty_list(self, mock_fetch):
        result = get_margin_trading("600519")
        assert result == []

    @patch("app.services.capital_service.fetch_margin_trading", return_value=MOCK_RAW_MARGIN)
    def test_margin_api_returns_semantic_fields(self, mock_fetch):
        """Integration: verify API endpoint returns semantic fields."""
        response = client.get("/api/v1/margin/600519")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        row = data["data"][0]
        assert "date" in row
        assert "rzye" in row
        assert "TRADE_DATE" not in row

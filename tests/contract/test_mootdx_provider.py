"""Contract tests for mootdx provider — all mocked since TCP is unavailable."""
from unittest.mock import patch, MagicMock

import pytest

from app.providers.mootdx_provider import (
    DependencyUnavailableError,
    fetch_finance_snapshot,
    fetch_f10,
    fetch_f10_announcement,
)


class TestFetchFinanceSnapshot:
    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_records(self, mock_client_factory):
        mock_client = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"eps": 1.5, "bvps": 10.2, "roe": 15.0, "profit": 100000000}
        ]
        mock_client.finance.return_value = mock_df
        mock_client_factory.return_value = mock_client

        result = fetch_finance_snapshot("688017")
        assert len(result) == 1
        assert result[0]["eps"] == 1.5

    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_empty_for_no_data(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.finance.return_value = None
        mock_client_factory.return_value = mock_client

        result = fetch_finance_snapshot("688017")
        assert result == []

    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_empty_for_empty_df(self, mock_client_factory):
        mock_client = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = True
        mock_client.finance.return_value = mock_df
        mock_client_factory.return_value = mock_client

        result = fetch_finance_snapshot("688017")
        assert result == []

    @patch("app.providers.mootdx_provider._get_client")
    def test_raises_on_query_failure(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.finance.side_effect = RuntimeError("TCP error")
        mock_client_factory.return_value = mock_client

        with pytest.raises(DependencyUnavailableError, match="finance query failed"):
            fetch_finance_snapshot("688017")


class TestFetchF10:
    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_text(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.F10.return_value = "公司简介：xxx"
        mock_client_factory.return_value = mock_client

        result = fetch_f10("688017", "公司概况")
        assert result == "公司简介：xxx"

    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_empty_string_for_none(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.F10.return_value = None
        mock_client_factory.return_value = mock_client

        result = fetch_f10("688017", "公司概况")
        assert result == ""

    @patch("app.providers.mootdx_provider._get_client")
    def test_raises_on_query_failure(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.F10.side_effect = RuntimeError("TCP error")
        mock_client_factory.return_value = mock_client

        with pytest.raises(DependencyUnavailableError, match="F10 query failed"):
            fetch_f10("688017", "公司概况")


class TestFetchF10Announcement:
    @patch("app.providers.mootdx_provider._get_client")
    def test_calls_f10_with_latest_tips(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.F10.return_value = "最新公告内容"
        mock_client_factory.return_value = mock_client

        result = fetch_f10_announcement("688017")
        assert result == "最新公告内容"
        mock_client.F10.assert_called_once_with(symbol="688017", name="最新提示")


class TestDependencyUnavailable:
    def test_error_has_correct_attributes(self):
        err = DependencyUnavailableError("test message")
        assert err.code == "DEPENDENCY_UNAVAILABLE"
        assert err.status_code == 503
        assert err.provider == "mootdx"
        assert err.message == "test message"


class TestFetchMootdxKline:
    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_records(self, mock_client_factory):
        mock_client = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"open": 10.0, "close": 11.0, "high": 11.5, "low": 9.8,
             "vol": 100000, "amount": 1100000.0, "datetime": "2026-05-28"}
        ]
        mock_client.bars.return_value = mock_df
        mock_client_factory.return_value = mock_client

        from app.providers.mootdx_provider import fetch_mootdx_kline
        result = fetch_mootdx_kline("688017", category="daily", offset=10)
        assert len(result) == 1
        assert result[0]["open"] == 10.0
        assert result[0]["close"] == 11.0
        mock_client.bars.assert_called_once_with(symbol="688017", category=4, offset=10)

    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_empty_for_no_data(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.bars.return_value = None
        mock_client_factory.return_value = mock_client

        from app.providers.mootdx_provider import fetch_mootdx_kline
        result = fetch_mootdx_kline("688017")
        assert result == []

    @patch("app.providers.mootdx_provider._get_client")
    def test_returns_empty_for_empty_df(self, mock_client_factory):
        mock_client = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = True
        mock_client.bars.return_value = mock_df
        mock_client_factory.return_value = mock_client

        from app.providers.mootdx_provider import fetch_mootdx_kline
        result = fetch_mootdx_kline("688017")
        assert result == []

    @patch("app.providers.mootdx_provider._get_client")
    def test_raises_on_query_failure(self, mock_client_factory):
        mock_client = MagicMock()
        mock_client.bars.side_effect = RuntimeError("TCP error")
        mock_client_factory.return_value = mock_client

        from app.providers.mootdx_provider import fetch_mootdx_kline
        with pytest.raises(DependencyUnavailableError, match="bars query failed"):
            fetch_mootdx_kline("688017")

    def test_invalid_category_raises(self):
        from app.providers.mootdx_provider import fetch_mootdx_kline
        with pytest.raises(DependencyUnavailableError, match="Invalid kline category"):
            fetch_mootdx_kline("688017", category="invalid")

    @patch("app.providers.mootdx_provider._get_client")
    def test_weekly_category_maps_to_5(self, mock_client_factory):
        mock_client = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [{"open": 10.0}]
        mock_client.bars.return_value = mock_df
        mock_client_factory.return_value = mock_client

        from app.providers.mootdx_provider import fetch_mootdx_kline
        fetch_mootdx_kline("688017", category="weekly")
        mock_client.bars.assert_called_once_with(symbol="688017", category=5, offset=100)

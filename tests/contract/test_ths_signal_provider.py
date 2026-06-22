"""Contract tests for THS hot stocks and northbound capital providers."""
import pytest
import responses

from app.core.errors import UpstreamSchemaError
from app.providers.ths import fetch_hot_stocks, fetch_northbound_realtime


class TestFetchHotStocks:
    @responses.activate
    def test_returns_stock_list(self):
        responses.add(
            responses.GET,
            "http://zx.10jqka.com.cn/event/api/getharden/date/2026-05-27/orderby/date/orderway/desc/charset/GBK/",
            json={
                "errocode": 0,
                "data": [
                    {
                        "code": "600519",
                        "name": "贵州茅台",
                        "reason": "白酒+消费复苏",
                        "close": "1800.00",
                        "zhangfu": "5.20",
                        "huanshou": "1.30",
                        "chengjiaoe": "5000000000",
                        "ddejingliang": "200000",
                        "market": "沪",
                    },
                ],
            },
            status=200,
        )
        result = fetch_hot_stocks("2026-05-27")
        assert len(result) == 1
        assert result[0]["code"] == "600519"
        assert result[0]["reason"] == "白酒+消费复苏"

    @responses.activate
    def test_handles_error_code(self):
        responses.add(
            responses.GET,
            "http://zx.10jqka.com.cn/event/api/getharden/date/2026-05-27/orderby/date/orderway/desc/charset/GBK/",
            json={"errocode": 1, "errormsg": "日期无效"},
            status=200,
        )
        with pytest.raises(UpstreamSchemaError, match="日期无效"):
            fetch_hot_stocks("2026-05-27")

    @responses.activate
    def test_handles_empty_data(self):
        responses.add(
            responses.GET,
            "http://zx.10jqka.com.cn/event/api/getharden/date/2026-05-27/orderby/date/orderway/desc/charset/GBK/",
            json={"errocode": 0, "data": []},
            status=200,
        )
        result = fetch_hot_stocks("2026-05-27")
        assert result == []

    @responses.activate
    def test_handles_invalid_json(self):
        responses.add(
            responses.GET,
            "http://zx.10jqka.com.cn/event/api/getharden/date/2026-05-27/orderby/date/orderway/desc/charset/GBK/",
            body="not json",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError, match="Failed to parse"):
            fetch_hot_stocks("2026-05-27")


class TestFetchNorthboundRealtime:
    @responses.activate
    def test_returns_time_series(self):
        responses.add(
            responses.GET,
            "https://data.hexin.cn/market/hsgtApi/method/dayChart/",
            json={
                "time": ["09:30", "09:31", "09:32"],
                "hgt": [1.2, 1.5, 1.8],
                "sgt": [0.8, 0.9, 1.1],
            },
            status=200,
        )
        result = fetch_northbound_realtime()
        assert len(result["time"]) == 3
        assert result["hgt"] == [1.2, 1.5, 1.8]
        assert result["sgt"] == [0.8, 0.9, 1.1]

    @responses.activate
    def test_handles_empty_data(self):
        responses.add(
            responses.GET,
            "https://data.hexin.cn/market/hsgtApi/method/dayChart/",
            json={"time": [], "hgt": [], "sgt": []},
            status=200,
        )
        result = fetch_northbound_realtime()
        assert result["time"] == []

    @responses.activate
    def test_handles_invalid_json(self):
        responses.add(
            responses.GET,
            "https://data.hexin.cn/market/hsgtApi/method/dayChart/",
            body="bad data",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError, match="Failed to parse"):
            fetch_northbound_realtime()

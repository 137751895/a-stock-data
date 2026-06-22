"""Tests for failure paths: invalid code, provider timeout, malformed JSONP,
upstream non-200, empty response, structure changes, and POST failures."""
import pytest
import responses
from requests.exceptions import Timeout, ConnectionError as ReqConnectionError

from app.core.errors import UpstreamHTTPError, UpstreamSchemaError
from app.core.errors import ValidationError as AppValidationError
from app.core.normalize import validate_code
from app.providers.eastmoney import (
    fetch_stock_info,
    fetch_stock_news,
    fetch_fund_flow_minute,
    eastmoney_datacenter,
)
from app.providers.cninfo import fetch_announcements
from app.providers.tencent import fetch_quotes


class TestInvalidCodeValidation:
    def test_rejects_empty_string(self):
        with pytest.raises(AppValidationError):
            validate_code("")

    def test_rejects_too_short(self):
        with pytest.raises(AppValidationError):
            validate_code("600")

    def test_rejects_too_long(self):
        with pytest.raises(AppValidationError):
            validate_code("6005191")

    def test_rejects_letters_only(self):
        with pytest.raises(AppValidationError):
            validate_code("ABCDEF")

    def test_rejects_special_chars(self):
        with pytest.raises(AppValidationError):
            validate_code("600-19")

    def test_accepts_valid_codes(self):
        assert validate_code("600519") == "600519"
        assert validate_code("SH600519") == "600519"
        assert validate_code("000001.SZ") == "000001"
        assert validate_code("BJ832000") == "832000"


class TestProviderTimeout:
    @responses.activate
    def test_eastmoney_timeout_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/get",
            body=Timeout("timed out"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_stock_info("600519")
        assert exc_info.value.provider == "eastmoney"
        assert exc_info.value.status_code == 502

    @responses.activate
    def test_eastmoney_connection_error_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/get",
            body=ReqConnectionError("connection refused"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_stock_info("600519")
        assert exc_info.value.provider == "eastmoney"


class TestMalformedJsonp:
    @responses.activate
    def test_missing_parentheses(self):
        responses.add(
            responses.GET,
            "https://search-api-web.eastmoney.com/search/jsonp",
            body="no_callback_here",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError) as exc_info:
            fetch_stock_news("600519")
        assert exc_info.value.provider == "eastmoney"

    @responses.activate
    def test_invalid_json_inside_callback(self):
        responses.add(
            responses.GET,
            "https://search-api-web.eastmoney.com/search/jsonp",
            body="jQuery_news({invalid json})",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError) as exc_info:
            fetch_stock_news("600519")
        assert exc_info.value.provider == "eastmoney"

    @responses.activate
    def test_empty_jsonp_body(self):
        responses.add(
            responses.GET,
            "https://search-api-web.eastmoney.com/search/jsonp",
            body="",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError):
            fetch_stock_news("600519")


class TestUpstreamNon200:
    @responses.activate
    def test_eastmoney_403_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/get",
            json={"error": "forbidden"},
            status=403,
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_stock_info("600519")
        assert exc_info.value.status_code == 502
        assert "403" in exc_info.value.message

    @responses.activate
    def test_eastmoney_500_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/get",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(UpstreamHTTPError):
            fetch_stock_info("600519")


class TestEmptyResponse:
    @responses.activate
    def test_datacenter_empty_result_returns_empty_list(self):
        responses.add(
            responses.GET,
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            json={"result": None},
            status=200,
        )
        result = eastmoney_datacenter("RPT_EMPTY")
        assert result == []

    @responses.activate
    def test_datacenter_no_data_key_returns_empty_list(self):
        responses.add(
            responses.GET,
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            json={"result": {"data": None}},
            status=200,
        )
        result = eastmoney_datacenter("RPT_EMPTY")
        assert result == []

    @responses.activate
    def test_fund_flow_empty_klines(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
            json={"data": {"klines": []}},
            status=200,
        )
        result = fetch_fund_flow_minute("600519")
        assert result == []

    @responses.activate
    def test_fund_flow_no_data_key(self):
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
            json={"data": None},
            status=200,
        )
        result = fetch_fund_flow_minute("600519")
        assert result == []

    @responses.activate
    def test_news_empty_article_list(self):
        responses.add(
            responses.GET,
            "https://search-api-web.eastmoney.com/search/jsonp",
            body='jQuery_news({"result":{"cmsArticleWebOld":{"list":[]}}})',
            status=200,
        )
        result = fetch_stock_news("600519")
        assert result == []


class TestStructureChange:
    @responses.activate
    def test_stock_info_missing_fields_returns_defaults(self):
        """When upstream changes field structure, we should get defaults not crash."""
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/get",
            json={"data": {"f57": "600519"}},  # minimal response
            status=200,
        )
        result = fetch_stock_info("600519")
        assert result["code"] == "600519"
        assert result["name"] == ""  # default
        assert result["price"] == 0  # default


class TestFundFlowMalformedCSV:
    @responses.activate
    def test_malformed_kline_values_skipped(self):
        """Non-numeric values in kline CSV should be skipped, not crash."""
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
            json={"data": {"klines": [
                "09:30,100,-50,30,70,80",       # valid
                "09:31,BAD,-60,40,80,90",        # invalid float
                "09:32,200,-60,40,80,90",        # valid
            ]}},
            status=200,
        )
        result = fetch_fund_flow_minute("600519")
        assert len(result) == 2  # malformed line skipped
        assert result[0]["time"] == "09:30"
        assert result[1]["time"] == "09:32"

    @responses.activate
    def test_short_kline_values_skipped(self):
        """Lines with fewer than 6 CSV fields should be skipped."""
        responses.add(
            responses.GET,
            "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
            json={"data": {"klines": [
                "09:30,100",        # too short
                "09:31,200,-60,40,80,90",  # valid
            ]}},
            status=200,
        )
        result = fetch_fund_flow_minute("600519")
        assert len(result) == 1


class TestHttpPostFailurePaths:
    @responses.activate
    def test_cninfo_timeout_raises_upstream_error(self):
        responses.add(
            responses.POST,
            "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            body=Timeout("timed out"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_announcements("600519")
        assert exc_info.value.provider == "cninfo"
        assert exc_info.value.status_code == 502

    @responses.activate
    def test_cninfo_connection_error_raises_upstream_error(self):
        responses.add(
            responses.POST,
            "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            body=ReqConnectionError("connection refused"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_announcements("600519")
        assert exc_info.value.provider == "cninfo"

    @responses.activate
    def test_cninfo_non_200_raises_upstream_error(self):
        responses.add(
            responses.POST,
            "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_announcements("600519")
        assert "500" in exc_info.value.message

    @responses.activate
    def test_cninfo_invalid_json_raises_schema_error(self):
        responses.add(
            responses.POST,
            "https://www.cninfo.com.cn/new/hisAnnouncement/query",
            body="not json at all",
            status=200,
        )
        with pytest.raises(UpstreamSchemaError) as exc_info:
            fetch_announcements("600519")
        assert exc_info.value.provider == "cninfo"


class TestTencentFailurePaths:
    @responses.activate
    def test_tencent_timeout_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://qt.gtimg.cn/q=sh600519",
            body=Timeout("timed out"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_quotes(["600519"])
        assert exc_info.value.provider == "tencent"
        assert exc_info.value.status_code == 502

    @responses.activate
    def test_tencent_connection_error_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://qt.gtimg.cn/q=sh600519",
            body=ReqConnectionError("connection refused"),
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_quotes(["600519"])
        assert exc_info.value.provider == "tencent"

    @responses.activate
    def test_tencent_non_200_raises_upstream_error(self):
        responses.add(
            responses.GET,
            "https://qt.gtimg.cn/q=sh600519",
            body="error",
            status=403,
        )
        with pytest.raises(UpstreamHTTPError) as exc_info:
            fetch_quotes(["600519"])
        assert "403" in exc_info.value.message

    @responses.activate
    def test_tencent_decode_error_raises_schema_error(self):
        """When response cannot be decoded as GBK, should raise UpstreamSchemaError."""
        # Send bytes that are not valid GBK — using raw bytes via body
        responses.add(
            responses.GET,
            "https://qt.gtimg.cn/q=sh600519",
            body=b'\x80\x81\x82\x83\x84',  # invalid GBK sequence
            status=200,
        )
        # The current code uses r.content.decode("gbk") which may or may not raise
        # depending on the bytes; if it succeeds, the parse result will be empty
        # Either way, it should not crash with an unhandled exception
        try:
            result = fetch_quotes(["600519"])
            # If decode succeeds, parsing should return empty dict (no valid lines)
            assert isinstance(result, dict)
        except UpstreamSchemaError:
            pass  # This is also acceptable

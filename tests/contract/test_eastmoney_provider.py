
import responses

from app.providers.eastmoney import (
    eastmoney_datacenter,
    fetch_reports,
    fetch_fund_flow_minute,
    fetch_margin_trading,
    fetch_stock_news,
    report_pdf_url,
)


@responses.activate
def test_eastmoney_datacenter_returns_data():
    responses.add(
        responses.GET,
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        json={"result": {"data": [{"TRADE_DATE": "2026-05-28", "AMOUNT": 100}]}},
        status=200,
    )
    result = eastmoney_datacenter("RPT_TEST", filter_str='(CODE="600519")')
    assert len(result) == 1
    assert result[0]["TRADE_DATE"] == "2026-05-28"


@responses.activate
def test_eastmoney_datacenter_handles_empty():
    responses.add(
        responses.GET,
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        json={"result": None},
        status=200,
    )
    result = eastmoney_datacenter("RPT_EMPTY")
    assert result == []


@responses.activate
def test_fetch_reports_returns_list():
    responses.add(
        responses.GET,
        "https://reportapi.eastmoney.com/report/list",
        json={"data": [{"title": "Test Report", "publishDate": "2026-05-28", "infoCode": "AP202605281234"}], "TotalPage": 1},
        status=200,
    )
    result = fetch_reports("600519")
    assert len(result) == 1
    assert result[0]["title"] == "Test Report"
    assert result[0]["pdf_url"] == "https://pdf.dfcfw.com/pdf/H3_AP202605281234_1.pdf"


@responses.activate
def test_fetch_reports_no_infocode_no_pdf_url():
    """Reports without infoCode should not have pdf_url."""
    responses.add(
        responses.GET,
        "https://reportapi.eastmoney.com/report/list",
        json={"data": [{"title": "No PDF"}], "TotalPage": 1},
        status=200,
    )
    result = fetch_reports("600519")
    assert "pdf_url" not in result[0]


def test_report_pdf_url_format():
    assert report_pdf_url("AP202605281234") == "https://pdf.dfcfw.com/pdf/H3_AP202605281234_1.pdf"


@responses.activate
def test_fetch_fund_flow_minute_returns_list():
    """CRITICAL: fund flow must use push2, not old Baidu PAE."""
    responses.add(
        responses.GET,
        "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
        json={"data": {"klines": ["09:30,100,-50,30,70,80", "09:31,200,-60,40,80,90"]}},
        status=200,
    )
    result = fetch_fund_flow_minute("600519")
    assert len(result) == 2
    assert result[0]["time"] == "09:30"
    assert result[0]["main_net"] == 100.0


@responses.activate
def test_fetch_fund_flow_minute_uses_push2_url():
    """Regression: must use push2.eastmoney.com, not baidu PAE."""
    responses.add(
        responses.GET,
        "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get",
        json={"data": {"klines": []}},
        status=200,
    )
    fetch_fund_flow_minute("600519")
    assert "push2.eastmoney.com" in responses.calls[0].request.url


@responses.activate
def test_fetch_margin_trading():
    responses.add(
        responses.GET,
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        json={"result": {"data": [{"TRADE_DATE": "2026-05-28", "RZYE": 1000000}]}},
        status=200,
    )
    result = fetch_margin_trading("600519")
    assert len(result) == 1


@responses.activate
def test_fetch_stock_news():
    jsonp_response = 'jQuery_news({"result":{"cmsArticleWebOld":{"list":[{"title":"Test <b>News</b>","content":"Content","date":"2026-05-28","mediaName":"Source","url":"http://test.com"}]}}})'
    responses.add(
        responses.GET,
        "https://search-api-web.eastmoney.com/search/jsonp",
        body=jsonp_response,
        status=200,
    )
    result = fetch_stock_news("600519")
    assert len(result) == 1
    assert result[0]["title"] == "Test News"  # HTML tags stripped
    assert result[0]["source"] == "Source"


@responses.activate
def test_fetch_stock_news_cms_direct_list():
    """Eastmoney actually returns cmsArticleWebOld as a list directly (SKILL v3.2.1 §5.1)."""
    jsonp_response = (
        'jQuery_news({"result":{"cmsArticleWebOld":'
        '[{"title":"Real <em>News</em>","content":"Body","date":"2026-06-01",'
        '"mediaName":"东方财富","url":"http://em.com"}]}})'
    )
    responses.add(
        responses.GET,
        "https://search-api-web.eastmoney.com/search/jsonp",
        body=jsonp_response,
        status=200,
    )
    result = fetch_stock_news("600519")
    assert len(result) == 1
    assert result[0]["title"] == "Real News"
    assert result[0]["source"] == "东方财富"

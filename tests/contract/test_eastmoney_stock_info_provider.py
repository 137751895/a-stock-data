import responses
from app.providers.eastmoney import fetch_stock_info


@responses.activate
def test_fetch_stock_info_returns_structured_data():
    responses.add(
        responses.GET,
        "https://push2.eastmoney.com/api/qt/stock/get",
        json={
            "data": {
                "f57": "600519",
                "f58": "贵州茅台",
                "f127": "白酒",
                "f84": 1256198000,
                "f85": 1256198000,
                "f116": 2260000000000,
                "f117": 2260000000000,
                "f189": "20010827",
                "f43": 1800.0,
            }
        },
        status=200,
    )
    result = fetch_stock_info("600519")
    assert result["code"] == "600519"
    assert result["name"] == "贵州茅台"
    assert result["industry"] == "白酒"
    assert result["list_date"] == "20010827"
    assert result["price"] == 1800.0


@responses.activate
def test_fetch_stock_info_handles_empty_data():
    responses.add(
        responses.GET,
        "https://push2.eastmoney.com/api/qt/stock/get",
        json={"data": None},
        status=200,
    )
    result = fetch_stock_info("999999")
    assert result["code"] == ""
    assert result["name"] == ""

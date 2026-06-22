import responses

from app.providers.cninfo import fetch_announcements, _cninfo_ts_to_date


class TestCninfoTsToDate:
    def test_unix_ms(self):
        # 2026-05-28 00:00:00 UTC = 1779926400000 ms
        result = _cninfo_ts_to_date(1779926400000)
        assert result.startswith("2026-05-2")

    def test_string_input(self):
        result = _cninfo_ts_to_date("2026-05-28 10:00:00")
        assert result == "2026-05-28"

    def test_none_input(self):
        result = _cninfo_ts_to_date(None)
        assert result == ""


@responses.activate
def test_fetch_announcements_uses_org_id():
    """CRITICAL REGRESSION: stock param must be 'code,orgId' format."""
    responses.add(
        responses.POST,
        "https://www.cninfo.com.cn/new/hisAnnouncement/query",
        json={"announcements": [
            {"announcementTitle": "Test Ann", "announcementTypeName": "公告",
             "announcementTime": 1779926400000, "announcementId": "123"}
        ]},
        status=200,
    )
    result = fetch_announcements("600519")
    assert len(result) == 1
    assert result[0]["title"] == "Test Ann"

    # Verify stock param format: code,orgId
    request_body = responses.calls[-1].request.body
    assert "600519%2Cgssh0600519" in request_body or "600519,gssh0600519" in request_body


@responses.activate
def test_fetch_announcements_shenzhen_org_id():
    responses.add(
        responses.POST,
        "https://www.cninfo.com.cn/new/hisAnnouncement/query",
        json={"announcements": []},
        status=200,
    )
    fetch_announcements("000001")
    request_body = responses.calls[-1].request.body
    assert "000001%2Cgssz0000001" in request_body or "000001,gssz0000001" in request_body


@responses.activate
def test_fetch_announcements_handles_empty():
    responses.add(
        responses.POST,
        "https://www.cninfo.com.cn/new/hisAnnouncement/query",
        json={"announcements": None},
        status=200,
    )
    result = fetch_announcements("600519")
    assert result == []


SZSE_STOCK_URL = "http://www.cninfo.com.cn/new/data/szse_stock.json"
QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"


@responses.activate
def test_fetch_announcements_uses_dynamic_orgid():
    """#19: real orgId comes from szse_stock.json, not the hardcoded gssh0{code} rule."""
    import app.providers.cninfo as cninfo_mod

    cninfo_mod._CNINFO_ORGID_MAP = {}
    try:
        responses.add(
            responses.GET,
            SZSE_STOCK_URL,
            json={"stockList": [{"code": "601318", "orgId": "9900002221"}]},
            status=200,
        )
        responses.add(responses.POST, QUERY_URL, json={"announcements": []}, status=200)
        fetch_announcements("601318")
        request_body = responses.calls[-1].request.body
        assert "601318%2C9900002221" in request_body or "601318,9900002221" in request_body
    finally:
        cninfo_mod._CNINFO_ORGID_MAP = {}


@responses.activate
def test_fetch_announcements_falls_back_when_mapping_unavailable():
    """If szse_stock.json is unreachable, fall back to the hardcoded gssh0{code} rule."""
    import app.providers.cninfo as cninfo_mod

    cninfo_mod._CNINFO_ORGID_MAP = {}
    try:
        # szse_stock.json GET is intentionally not registered -> fetch fails -> fallback.
        responses.add(responses.POST, QUERY_URL, json={"announcements": []}, status=200)
        fetch_announcements("600519")
        request_body = responses.calls[-1].request.body
        assert "600519%2Cgssh0600519" in request_body or "600519,gssh0600519" in request_body
    finally:
        cninfo_mod._CNINFO_ORGID_MAP = {}

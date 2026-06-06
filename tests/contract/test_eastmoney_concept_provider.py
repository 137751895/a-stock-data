import responses

from app.providers.eastmoney import fetch_concept_blocks


SLIST_URL = "https://push2.eastmoney.com/api/qt/slist/get"


def _mock_slist_response():
    """Realistic Eastmoney slist response (boards mixed: industry/concept/region)."""
    return {
        "data": {
            "diff": {
                "0": {"f12": "BK0438", "f14": "食品饮料", "f3": "2.15", "f128": "贵州茅台"},
                "1": {"f12": "BK0477", "f14": "白酒", "f3": "3.20", "f128": "贵州茅台"},
                "2": {"f12": "BK0153", "f14": "贵州板块", "f3": "0.80", "f128": "贵州茅台"},
            }
        }
    }


@responses.activate
def test_fetch_concept_blocks_parses_correctly():
    responses.add(responses.GET, SLIST_URL, json=_mock_slist_response(), status=200)
    result = fetch_concept_blocks("600519")
    assert result["total"] == 3
    assert len(result["boards"]) == 3
    assert result["boards"][0]["name"] == "食品饮料"
    assert result["boards"][0]["code"] == "BK0438"
    assert result["boards"][0]["change_pct"] == "2.15"
    assert result["boards"][0]["lead_stock"] == "贵州茅台"
    assert "白酒" in result["concept_tags"]
    assert "贵州板块" in result["concept_tags"]


@responses.activate
def test_fetch_concept_blocks_diff_as_list():
    """slist diff may also come back as a list rather than a dict."""
    payload = {"data": {"diff": [
        {"f12": "BK0438", "f14": "食品饮料", "f3": "2.15", "f128": "贵州茅台"},
    ]}}
    responses.add(responses.GET, SLIST_URL, json=payload, status=200)
    result = fetch_concept_blocks("600519")
    assert result["total"] == 1
    assert result["concept_tags"] == ["食品饮料"]


@responses.activate
def test_fetch_concept_blocks_empty_result():
    responses.add(responses.GET, SLIST_URL, json={"data": None}, status=200)
    result = fetch_concept_blocks("600519")
    assert result == {"total": 0, "boards": [], "concept_tags": []}

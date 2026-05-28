import pytest
import responses

from app.core.errors import UpstreamSchemaError
from app.providers.baidu import fetch_concept_blocks


BAIDU_CONCEPT_URL = "https://finance.pae.baidu.com/api/getrelatedblock"


def _mock_concept_response():
    """Return a realistic Baidu concept blocks response."""
    return {
        "ResultCode": 0,
        "Result": [
            {
                "type": "行业板块",
                "list": [
                    {"name": "半导体", "increase": "2.15", "desc": "申万二级"},
                    {"name": "电子", "increase": "1.80", "desc": "申万一级"},
                ],
            },
            {
                "type": "概念板块",
                "list": [
                    {"name": "芯片", "increase": "3.20", "desc": ""},
                    {"name": "国产替代", "increase": "1.50", "desc": ""},
                ],
            },
            {
                "type": "地域板块",
                "list": [
                    {"name": "上海", "increase": "0.80", "desc": ""},
                ],
            },
        ],
    }


@responses.activate
def test_fetch_concept_blocks_parses_correctly():
    responses.add(
        responses.GET,
        BAIDU_CONCEPT_URL,
        json=_mock_concept_response(),
        status=200,
    )
    result = fetch_concept_blocks("688017")
    assert len(result["industry"]) == 2
    assert result["industry"][0]["name"] == "半导体"
    assert len(result["concept"]) == 2
    assert "芯片" in result["concept_tags"]
    assert "国产替代" in result["concept_tags"]
    assert len(result["region"]) == 1
    assert result["region"][0]["name"] == "上海"


@responses.activate
def test_fetch_concept_blocks_string_result_code():
    """ResultCode can be string '0' instead of int 0."""
    data = _mock_concept_response()
    data["ResultCode"] = "0"
    responses.add(
        responses.GET,
        BAIDU_CONCEPT_URL,
        json=data,
        status=200,
    )
    result = fetch_concept_blocks("688017")
    assert len(result["industry"]) == 2


@responses.activate
def test_fetch_concept_blocks_error_result_code():
    responses.add(
        responses.GET,
        BAIDU_CONCEPT_URL,
        json={"ResultCode": -1, "Result": []},
        status=200,
    )
    with pytest.raises(UpstreamSchemaError, match="Baidu PAE error"):
        fetch_concept_blocks("688017")


@responses.activate
def test_fetch_concept_blocks_empty_result():
    responses.add(
        responses.GET,
        BAIDU_CONCEPT_URL,
        json={"ResultCode": 0, "Result": []},
        status=200,
    )
    result = fetch_concept_blocks("688017")
    assert result == {"industry": [], "concept": [], "region": [], "concept_tags": []}


@responses.activate
def test_fetch_concept_blocks_invalid_json():
    responses.add(
        responses.GET,
        BAIDU_CONCEPT_URL,
        body="not json",
        status=200,
    )
    with pytest.raises(UpstreamSchemaError, match="Failed to parse"):
        fetch_concept_blocks("688017")

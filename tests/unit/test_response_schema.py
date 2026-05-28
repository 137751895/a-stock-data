from app.schemas.common import success_response, error_response


def test_success_response_structure():
    resp = success_response(data={"price": 100}, source=["tencent"])
    assert resp["success"] is True
    assert resp["data"] == {"price": 100}
    assert resp["source"] == ["tencent"]
    assert resp["warnings"] == []
    assert "request_id" in resp
    assert "fetched_at" in resp
    assert resp["error"] is None


def test_success_response_with_warnings():
    resp = success_response(data={}, warnings=["eps missing"])
    assert resp["warnings"] == ["eps missing"]


def test_error_response_structure():
    resp = error_response(code="UPSTREAM_HTTP_ERROR", message="403 forbidden", provider="eastmoney")
    assert resp["success"] is False
    assert resp["error"]["code"] == "UPSTREAM_HTTP_ERROR"
    assert resp["error"]["message"] == "403 forbidden"
    assert resp["error"]["provider"] == "eastmoney"
    assert resp["data"] is None

"""Tests for HTTP retry mechanism in core/http.py.

Verifies that:
1. create_session() builds a session with retry adapter mounted
2. Transient 500/502/503/504 errors are retried automatically
3. Non-retryable errors (e.g. 403, 404) are NOT retried
4. Retry works for both GET and POST
5. After all retries exhausted, UpstreamHTTPError is raised
"""
import responses
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.http import create_session, http_get, http_post, _session
from app.core.errors import UpstreamHTTPError
import app.core.http as http_module
import pytest


class TestCreateSessionRetry:
    def test_session_has_retry_adapter(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert isinstance(adapter, HTTPAdapter)
        assert isinstance(adapter.max_retries, Retry)

    def test_retry_total_matches_config(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 2  # default_retry_count

    def test_retry_covers_server_errors(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert 500 in adapter.max_retries.status_forcelist
        assert 502 in adapter.max_retries.status_forcelist
        assert 503 in adapter.max_retries.status_forcelist
        assert 504 in adapter.max_retries.status_forcelist

    def test_retry_allows_post(self):
        session = create_session()
        adapter = session.get_adapter("https://example.com")
        assert "POST" in adapter.max_retries.allowed_methods

    def test_http_adapter_mounted_for_both_schemes(self):
        session = create_session()
        https_adapter = session.get_adapter("https://example.com")
        http_adapter = session.get_adapter("http://example.com")
        assert isinstance(https_adapter, HTTPAdapter)
        assert isinstance(http_adapter, HTTPAdapter)


class TestRetryOnTransientFailure:
    """Test that transient server errors trigger retries."""

    def setup_method(self):
        """Reset global session before each test to pick up fresh adapter."""
        http_module._session = None

    @responses.activate
    def test_get_retries_on_502_then_succeeds(self):
        """First call returns 502, second returns 200 — should succeed."""
        url = "https://test-retry.example.com/data"
        responses.add(responses.GET, url, json={"error": "bad gateway"}, status=502)
        responses.add(responses.GET, url, json={"result": "ok"}, status=200)

        resp = http_get(url, provider="test")
        assert resp.json() == {"result": "ok"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_post_retries_on_503_then_succeeds(self):
        """POST also retries on transient failure."""
        url = "https://test-retry.example.com/post"
        responses.add(responses.POST, url, json={"error": "unavailable"}, status=503)
        responses.add(responses.POST, url, json={"result": "ok"}, status=200)

        resp = http_post(url, json={"key": "val"}, provider="test")
        assert resp.json() == {"result": "ok"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_get_raises_after_all_retries_exhausted(self):
        """After total retries exhausted, should raise UpstreamHTTPError."""
        url = "https://test-retry.example.com/fail"
        # default_retry_count=2, so total attempts = 1 original + 2 retries = 3
        responses.add(responses.GET, url, json={"error": "fail"}, status=502)
        responses.add(responses.GET, url, json={"error": "fail"}, status=502)
        responses.add(responses.GET, url, json={"error": "fail"}, status=502)

        with pytest.raises(UpstreamHTTPError) as exc_info:
            http_get(url, provider="test")
        assert "502" in exc_info.value.message

    @responses.activate
    def test_get_does_not_retry_on_403(self):
        """Client errors (403) should NOT be retried."""
        url = "https://test-retry.example.com/auth"
        responses.add(responses.GET, url, json={"error": "forbidden"}, status=403)

        with pytest.raises(UpstreamHTTPError) as exc_info:
            http_get(url, provider="test")
        assert "403" in exc_info.value.message
        assert len(responses.calls) == 1  # No retry

    @responses.activate
    def test_get_does_not_retry_on_404(self):
        """404 should NOT be retried."""
        url = "https://test-retry.example.com/missing"
        responses.add(responses.GET, url, json={"error": "not found"}, status=404)

        with pytest.raises(UpstreamHTTPError):
            http_get(url, provider="test")
        assert len(responses.calls) == 1

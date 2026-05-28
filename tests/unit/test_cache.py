"""Tests for the minimal file-based TTL cache layer.

Tests cover:
1. cache_get returns None on miss
2. cache_set + cache_get returns cached data
3. TTL expiration works
4. Disabled cache (empty cache_dir) returns None
5. Corrupted cache file is handled gracefully
6. Cache integrates correctly with services (stock_info, reports)
"""
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.cache import cache_get, cache_set, _cache_key


class TestCacheBasics:
    def test_cache_miss_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                result = cache_get("test", "nonexistent", ttl_seconds=60)
                assert result is None

    def test_cache_set_then_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                data = {"code": "600519", "name": "贵州茅台"}
                cache_set("test", "600519", data)
                result = cache_get("test", "600519", ttl_seconds=60)
                assert result == data

    def test_cache_ttl_expiration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                cache_set("test", "expire", {"value": 1})
                # TTL of 0 means immediately expired
                result = cache_get("test", "expire", ttl_seconds=0)
                assert result is None

    def test_cache_disabled_returns_none(self):
        """When cache_dir is empty string, caching is disabled."""
        with patch("app.core.config.settings.cache_dir", ""):
            cache_set("test", "key", {"data": 1})
            result = cache_get("test", "key", ttl_seconds=60)
            assert result is None

    def test_corrupted_cache_file_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                # Write corrupted file
                key_file = Path(tmpdir) / _cache_key("test", "bad")
                key_file.write_text("not valid json{{{")
                result = cache_get("test", "bad", ttl_seconds=60)
                assert result is None
                # Corrupted file should be cleaned up
                assert not key_file.exists()

    def test_cache_list_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                data = [{"title": "Report A"}, {"title": "Report B"}]
                cache_set("reports", "600519", data)
                result = cache_get("reports", "600519", ttl_seconds=60)
                assert result == data
                assert len(result) == 2

    def test_cache_key_is_deterministic(self):
        k1 = _cache_key("ns", "key")
        k2 = _cache_key("ns", "key")
        assert k1 == k2

    def test_different_namespaces_dont_collide(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.core.config.settings.cache_dir", tmpdir):
                cache_set("ns1", "key", {"from": "ns1"})
                cache_set("ns2", "key", {"from": "ns2"})
                assert cache_get("ns1", "key", ttl_seconds=60) == {"from": "ns1"}
                assert cache_get("ns2", "key", ttl_seconds=60) == {"from": "ns2"}


class TestCacheServiceIntegration:
    """Test that cache integrates with service layer."""

    def test_stock_info_returns_cached_flag_false_on_miss(self):
        from unittest.mock import patch as mock_patch
        import responses

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock_patch("app.core.config.settings.cache_dir", tmpdir):
                with responses.RequestsMock() as rsps:
                    rsps.add(
                        responses.GET,
                        "https://push2.eastmoney.com/api/qt/stock/get",
                        json={"data": {"f57": "600519", "f58": "贵州茅台"}},
                        status=200,
                    )
                    from app.services.fundamentals_service import get_stock_info
                    import app.core.http as http_module
                    http_module._session = None
                    data, cached = get_stock_info("600519")
                    assert cached is False
                    assert data["code"] == "600519"

    def test_stock_info_returns_cached_flag_true_on_hit(self):
        from unittest.mock import patch as mock_patch

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock_patch("app.core.config.settings.cache_dir", tmpdir):
                # Pre-populate cache
                cache_set("stock_info", "600519", {"code": "600519", "name": "贵州茅台"})
                from app.services.fundamentals_service import get_stock_info
                data, cached = get_stock_info("600519")
                assert cached is True
                assert data["code"] == "600519"

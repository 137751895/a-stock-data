"""Contract tests for iwencai provider."""
import pytest
import responses

from app.core.errors import ProviderAuthError, UpstreamSchemaError
from app.providers.iwencai import fetch_iwencai_search, dedup_articles, _ensure_api_key


class TestEnsureApiKey:
    def test_raises_when_no_key(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "")
        with pytest.raises(ProviderAuthError, match="IWENCAI_API_KEY"):
            _ensure_api_key()

    def test_returns_key_when_set(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "test-key-123")
        assert _ensure_api_key() == "test-key-123"


class TestFetchIwencaiSearch:
    @responses.activate
    def test_returns_articles(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "test-key")
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_base_url", "https://mock-iwencai.test")
        responses.add(
            responses.POST,
            "https://mock-iwencai.test/v1/comprehensive/search",
            json={"status_code": 0, "data": [
                {"uid": "1", "title": "Report A", "publish_date": "2026-05-28", "score": 0.9},
                {"uid": "2", "title": "Report B", "publish_date": "2026-05-27", "score": 0.8},
            ]},
            status=200,
        )
        result = fetch_iwencai_search("test query")
        assert len(result) == 2
        assert result[0]["title"] == "Report A"

    @responses.activate
    def test_handles_api_error(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "test-key")
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_base_url", "https://mock-iwencai.test")
        responses.add(
            responses.POST,
            "https://mock-iwencai.test/v1/comprehensive/search",
            json={"status_code": 1, "status_msg": "invalid query"},
            status=200,
        )
        with pytest.raises(UpstreamSchemaError, match="invalid query"):
            fetch_iwencai_search("bad query")

    @responses.activate
    def test_handles_empty_data(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "test-key")
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_base_url", "https://mock-iwencai.test")
        responses.add(
            responses.POST,
            "https://mock-iwencai.test/v1/comprehensive/search",
            json={"status_code": 0, "data": None},
            status=200,
        )
        result = fetch_iwencai_search("empty query")
        assert result == []

    def test_raises_without_key(self, monkeypatch):
        monkeypatch.setattr("app.providers.iwencai.settings.iwencai_api_key", "")
        with pytest.raises(ProviderAuthError, match="IWENCAI_API_KEY"):
            fetch_iwencai_search("test query")


class TestDedupArticles:
    def test_dedup_keeps_highest_score(self):
        articles = [
            {"uid": "1", "title": "A", "publish_date": "2026-05-28", "score": 0.5},
            {"uid": "1", "title": "A", "publish_date": "2026-05-28", "score": 0.9},
            {"uid": "2", "title": "B", "publish_date": "2026-05-27", "score": 0.8},
        ]
        result = dedup_articles(articles)
        assert len(result) == 2
        # Should keep higher score for uid=1
        uid1 = [a for a in result if a["uid"] == "1"][0]
        assert uid1["score"] == 0.9

    def test_dedup_empty(self):
        assert dedup_articles([]) == []

    def test_dedup_sorts_by_date(self):
        articles = [
            {"uid": "1", "title": "A", "publish_date": "2026-05-25", "score": 0.9},
            {"uid": "2", "title": "B", "publish_date": "2026-05-28", "score": 0.8},
        ]
        result = dedup_articles(articles)
        assert result[0]["publish_date"] == "2026-05-28"

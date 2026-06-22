"""Global test configuration.

Disables file-based caching during tests to prevent cross-test interference.
Individual cache tests can override this by patching settings.cache_dir.
"""
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def disable_cache():
    """Disable file cache for all tests by default."""
    with patch("app.core.config.settings.cache_dir", ""):
        yield

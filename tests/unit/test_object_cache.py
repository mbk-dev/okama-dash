import os
import pickle
import time
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit

CACHE_MODULE = "common.object_cache"


@pytest.fixture
def cache_dir(tmp_path):
    with patch(f"{CACHE_MODULE}._cache_dir", tmp_path):
        yield tmp_path


@pytest.fixture
def _no_cleanup():
    with patch(f"{CACHE_MODULE}.cleanup_expired_files"):
        yield


class TestBuildCacheKey:
    def test_sorted_symbols(self, cache_dir):
        from common.object_cache import _build_cache_key

        key1 = _build_cache_key("assetlist", {"symbols": ["SPY.US", "TLT.US"], "ccy": "USD"})
        key2 = _build_cache_key("assetlist", {"symbols": ["TLT.US", "SPY.US"], "ccy": "USD"})
        assert key1 == key2

    def test_sorted_symbols_with_weights(self, cache_dir):
        from common.object_cache import _build_cache_key

        key1 = _build_cache_key(
            "portfolio",
            {
                "symbols": ["SPY.US", "TLT.US"],
                "weights": [0.6, 0.4],
            },
        )
        key2 = _build_cache_key(
            "portfolio",
            {
                "symbols": ["TLT.US", "SPY.US"],
                "weights": [0.4, 0.6],
            },
        )
        assert key1 == key2

    def test_includes_okama_version(self, cache_dir):
        from common.object_cache import _build_cache_key

        key = _build_cache_key("assetlist", {"symbols": ["SPY.US"], "ccy": "USD"})
        assert "okv=" in key

    def test_deterministic(self, cache_dir):
        from common.object_cache import _build_cache_key

        params = {"symbols": ["SPY.US", "BND.US"], "ccy": "USD", "first_date": "2020-01"}
        key1 = _build_cache_key("assetlist", params)
        key2 = _build_cache_key("assetlist", params)
        assert key1 == key2

    def test_different_params_different_keys(self, cache_dir):
        from common.object_cache import _build_cache_key

        key1 = _build_cache_key("assetlist", {"symbols": ["SPY.US"], "ccy": "USD"})
        key2 = _build_cache_key("assetlist", {"symbols": ["SPY.US"], "ccy": "EUR"})
        assert key1 != key2

    def test_ends_with_pkl(self, cache_dir):
        from common.object_cache import _build_cache_key

        key = _build_cache_key("assetlist", {"symbols": ["SPY.US"]})
        assert key.endswith(".pkl")


# Filesystem NAME_MAX: a single path component may not exceed 255 bytes.
_LONG_PORTFOLIO_PARAMS = {
    "symbols": ["OKID10.INDX", "MCFTR.INDX", "RUCBTRNS.INDX", "GC.COMM"],
    "weights": [0.5, 0.2, 0.1, 0.2],
    "ccy": "RUB",
    "first_date": "2000-01",
    "last_date": "2026-05",
    "rebal": "year",
    "abs_dev": 10,
    "rel_dev": 50,
    "cf_strategy": "percentage",
    "cf_freq": "month",
    "inflation": False,
    "initial_amount": 1000,
    "cashflow_hash": "1cfee93f5ae5",
}


class TestBuildCacheKeyLength:
    def test_long_key_stays_within_filesystem_limit(self, cache_dir):
        from common.object_cache import _build_cache_key

        key = _build_cache_key("portfolio", _LONG_PORTFOLIO_PARAMS)
        assert len(key.encode("utf-8")) <= 255

    def test_long_key_is_deterministic(self, cache_dir):
        from common.object_cache import _build_cache_key

        key1 = _build_cache_key("portfolio", _LONG_PORTFOLIO_PARAMS)
        key2 = _build_cache_key("portfolio", _LONG_PORTFOLIO_PARAMS)
        assert key1 == key2

    def test_long_keys_with_different_params_differ(self, cache_dir):
        from common.object_cache import _build_cache_key

        other = {**_LONG_PORTFOLIO_PARAMS, "ccy": "USD"}
        key1 = _build_cache_key("portfolio", _LONG_PORTFOLIO_PARAMS)
        key2 = _build_cache_key("portfolio", other)
        assert key1 != key2

    def test_long_key_keeps_pkl_and_version(self, cache_dir):
        from common.object_cache import _build_cache_key, CACHE_FORMAT_VERSION

        key = _build_cache_key("portfolio", _LONG_PORTFOLIO_PARAMS)
        # cleanup_expired_files() only sweeps files carrying the cv marker
        assert key.endswith(".pkl")
        assert f"cv={CACHE_FORMAT_VERSION}" in key

    def test_short_key_remains_human_readable(self, cache_dir):
        from common.object_cache import _build_cache_key

        key = _build_cache_key("assetlist", {"symbols": ["SPY.US"], "ccy": "USD"})
        assert "SPY.US" in key


class TestGetOrCreate:
    def test_cache_miss_calls_constructor(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create

        calls = []

        def constructor():
            calls.append(1)
            return {"data": "test"}

        obj, key = get_or_create(
            obj_type="assetlist",
            constructor_fn=constructor,
            cache_key_params={"symbols": ["SPY.US"], "ccy": "USD"},
            ttl_seconds=3600,
        )
        assert obj == {"data": "test"}
        assert len(calls) == 1
        assert (cache_dir / key).exists()

    def test_cache_hit_skips_constructor(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create

        calls = []

        def constructor():
            calls.append(1)
            return {"data": "test"}

        params = {"symbols": ["SPY.US"], "ccy": "USD"}
        get_or_create("assetlist", constructor, params, ttl_seconds=3600)
        get_or_create("assetlist", constructor, params, ttl_seconds=3600)
        assert len(calls) == 1

    def test_expired_entry_calls_constructor(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create, _build_cache_key

        calls = []

        def constructor():
            calls.append(1)
            return {"data": f"v{len(calls)}"}

        params = {"symbols": ["SPY.US"], "ccy": "USD"}
        get_or_create("assetlist", constructor, params, ttl_seconds=1)

        key = _build_cache_key("assetlist", params)
        file_path = cache_dir / key
        old_time = time.time() - 10
        os.utime(file_path, (old_time, old_time))

        with patch(f"{CACHE_MODULE}._lru_load") as mock_lru:
            mock_lru.side_effect = lambda k, m: pickle.loads((cache_dir / k).read_bytes())
            obj, _ = get_or_create("assetlist", constructor, params, ttl_seconds=1)

        assert len(calls) == 2
        assert obj == {"data": "v2"}

    def test_corrupt_file_reconstructs(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create, _build_cache_key

        params = {"symbols": ["SPY.US"], "ccy": "USD"}
        key = _build_cache_key("assetlist", params)
        file_path = cache_dir / key
        file_path.write_bytes(b"not a pickle")

        obj, _ = get_or_create(
            "assetlist",
            lambda: {"fresh": True},
            params,
            ttl_seconds=3600,
        )
        assert obj == {"fresh": True}

    def test_long_key_config_is_cached(self, cache_dir, _no_cleanup):
        # Reproduces the ENAMETOOLONG bug: a portfolio with long ticker names
        # plus cashflow params produced a >255-byte filename, so the cache
        # write silently failed and every Submit recomputed the object.
        from common.object_cache import get_or_create

        calls = []

        def constructor():
            calls.append(1)
            return {"data": "test"}

        get_or_create("portfolio", constructor, _LONG_PORTFOLIO_PARAMS, ttl_seconds=3600)
        obj, key = get_or_create("portfolio", constructor, _LONG_PORTFOLIO_PARAMS, ttl_seconds=3600)

        assert obj == {"data": "test"}
        assert len(calls) == 1
        assert (cache_dir / key).exists()

    def test_returns_cache_key_string(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create

        _, key = get_or_create(
            "assetlist",
            lambda: "obj",
            {"symbols": ["SPY.US"]},
            ttl_seconds=3600,
        )
        assert isinstance(key, str)
        assert key.endswith(".pkl")


class TestLoadCached:
    def test_loads_existing_file(self, cache_dir, _no_cleanup):
        from common.object_cache import get_or_create, load_cached

        _, key = get_or_create(
            "assetlist",
            lambda: {"value": 42},
            {"symbols": ["SPY.US"]},
            ttl_seconds=3600,
        )
        obj = load_cached(key)
        assert obj == {"value": 42}

    def test_missing_file_raises(self, cache_dir):
        from common.object_cache import load_cached

        with pytest.raises(FileNotFoundError):
            load_cached("nonexistent.pkl")


class TestCleanup:
    def test_removes_expired_files(self, cache_dir):
        from common.object_cache import cleanup_expired_files, CACHE_FORMAT_VERSION

        expired = cache_dir / f"test-cv={CACHE_FORMAT_VERSION}.pkl"
        expired.write_bytes(pickle.dumps("old"))
        old_time = time.time() - 40 * 24 * 3600
        os.utime(expired, (old_time, old_time))

        cleanup_expired_files(max_ttl_seconds=30 * 24 * 3600, _force=True)

        assert not expired.exists()

    def test_keeps_fresh_files(self, cache_dir):
        from common.object_cache import cleanup_expired_files, CACHE_FORMAT_VERSION

        fresh = cache_dir / f"test-cv={CACHE_FORMAT_VERSION}.pkl"
        fresh.write_bytes(pickle.dumps("new"))

        cleanup_expired_files(max_ttl_seconds=30 * 24 * 3600, _force=True)

        assert fresh.exists()

    def test_ignores_legacy_files(self, cache_dir):
        from common.object_cache import cleanup_expired_files

        legacy = cache_dir / "old-format-ef-base-v2.pkl"
        legacy.write_bytes(pickle.dumps("legacy"))
        old_time = time.time() - 40 * 24 * 3600
        os.utime(legacy, (old_time, old_time))

        cleanup_expired_files(max_ttl_seconds=30 * 24 * 3600, _force=True)

        assert legacy.exists()


class TestCacheIsolation:
    """
    Cache-isolation tests for object_cache pickles.

    When the app runs with mocked okama (TESTING=1, e.g. during E2E tests)
    it must NOT write mock pickles into the same cache slots the real app
    reads from — otherwise the production app could serve mock data.
    """

    def test_testing_key_differs_from_production_key(self, cache_dir, monkeypatch):
        from common.object_cache import _build_cache_key

        params = {"symbols": ["SPY.US", "TLT.US"], "ccy": "USD"}

        # Production key (no TESTING env var)
        monkeypatch.delenv("TESTING", raising=False)
        prod_key = _build_cache_key("assetlist", params)

        # Test key (TESTING=1)
        monkeypatch.setenv("TESTING", "1")
        test_key = _build_cache_key("assetlist", params)

        assert test_key != prod_key

    def test_testing_key_contains_test_discriminator(self, cache_dir, monkeypatch):
        from common.object_cache import _build_cache_key

        monkeypatch.setenv("TESTING", "1")
        key = _build_cache_key("assetlist", {"symbols": ["SPY.US"]})

        # Should contain a test discriminator, not okama version
        assert "test" in key
        assert "okv=" not in key or "okv=test" in key

    def test_production_key_unchanged(self, cache_dir, monkeypatch):
        from common.object_cache import _build_cache_key

        monkeypatch.delenv("TESTING", raising=False)
        params = {"symbols": ["SPY.US"], "ccy": "USD"}
        key = _build_cache_key("assetlist", params)

        # Should contain okama version, same as before
        assert "okv=" in key
        assert "test" not in key or "latest" in key  # "test" might appear in okv if okama.__version__ contains it

"""Cache-isolation tests for the symbol indices.

The symbol indices are memoized for 30 days. When the app runs with mocked
okama (``TESTING=1``, e.g. during E2E tests) it must NOT write its mock-built
index into the same cache store the real app reads from — otherwise the real
app serves an index built from a handful of fixture tickers and real tickers
(OKID.INDX, AGG.US, GC.COMM, ...) disappear from every searchable dropdown.
"""

import okama
import pandas as pd
import pytest
from flask import Flask

import common
import common.symbols as symbols_mod

pytestmark = pytest.mark.unit


def _frame(rows: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["symbol", "name"]).astype("string")


def _patch_okama(monkeypatch, frames_by_ns: dict[str, pd.DataFrame]) -> None:
    namespaces = list(frames_by_ns)
    monkeypatch.setattr("okama.assets_namespaces", namespaces)
    monkeypatch.setattr("okama.symbols_in_namespace", lambda ns, *a, **k: frames_by_ns[ns.upper()])
    monkeypatch.setattr("common.settings.get_namespaces", lambda: namespaces)


class TestDataSourceToken:
    def test_token_is_test_when_testing(self, monkeypatch):
        monkeypatch.setenv("TESTING", "1")
        assert symbols_mod._data_source_token() == "test"

    def test_token_is_okama_version_when_not_testing(self, monkeypatch):
        monkeypatch.delenv("TESTING", raising=False)
        assert symbols_mod._data_source_token() == okama.__version__


class TestCacheIsolation:
    def test_mock_index_does_not_poison_real_index(self, monkeypatch):
        app = Flask(__name__)
        common.cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})
        with app.app_context():
            # 1) Mocked okama under TESTING builds and caches a small index.
            monkeypatch.setenv("TESTING", "1")
            _patch_okama(monkeypatch, {"US": _frame([("AAA.US", "Alpha")])})
            mock_index = symbols_mod.get_symbol_options_index()
            assert [opt["value"] for opt in mock_index["options"]] == ["AAA.US"]

            # 2) Real okama (no TESTING) with a different, larger dataset must
            #    NOT receive the cached mock index.
            monkeypatch.delenv("TESTING", raising=False)
            _patch_okama(
                monkeypatch,
                {
                    "US": _frame([("AAA.US", "Alpha")]),
                    "INDX": _frame([("OKID.INDX", "Russian bank deposit index OKID")]),
                },
            )
            real_index = symbols_mod.get_symbol_options_index()
            values = [opt["value"] for opt in real_index["options"]]
            assert "OKID.INDX" in values

    def test_real_search_index_isolated_from_mock(self, monkeypatch):
        app = Flask(__name__)
        common.cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})
        with app.app_context():
            monkeypatch.setenv("TESTING", "1")
            _patch_okama(monkeypatch, {"US": _frame([("AAA.US", "Alpha")])})
            assert symbols_mod.get_symbol_search_index()["symbols"] == ["AAA.US"]

            monkeypatch.delenv("TESTING", raising=False)
            _patch_okama(
                monkeypatch,
                {
                    "US": _frame([("AAA.US", "Alpha")]),
                    "INDX": _frame([("OKID.INDX", "Russian bank deposit index OKID")]),
                },
            )
            assert "OKID.INDX" in symbols_mod.get_symbol_search_index()["symbols"]

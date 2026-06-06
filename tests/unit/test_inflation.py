"""Currency-list helpers: URL ccy resolution and the cached INFL lookup."""

import pandas as pd
import pytest
from flask import Flask

import common
import common.inflation as inflation_mod
from common.inflation import resolve_url_currency

pytestmark = pytest.mark.unit

CURRENCIES = ["USD", "EUR", "RUB"]


def _infl_frame(codes: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"symbol": [f"{c}.INFL" for c in codes], "name": codes})


class TestResolveUrlCurrency:
    def test_lowercase_known_currency_uppercased(self):
        assert resolve_url_currency("usd", CURRENCIES) == "USD"

    def test_mixed_case_known_currency_uppercased(self):
        assert resolve_url_currency("rUb", CURRENCIES) == "RUB"

    def test_uppercase_known_currency_passes_through(self):
        assert resolve_url_currency("EUR", CURRENCIES) == "EUR"

    def test_unknown_currency_falls_back_to_default(self):
        assert resolve_url_currency("xyz", CURRENCIES) == "USD"

    def test_none_falls_back_to_default(self):
        assert resolve_url_currency(None, CURRENCIES) == "USD"

    def test_custom_default(self):
        assert resolve_url_currency("xyz", CURRENCIES, default="RUB") == "RUB"

    def test_empty_currency_list_falls_back_to_default(self):
        assert resolve_url_currency("usd", []) == "USD"


class TestCurrencyListCaching:
    """The INFL lookup is memoized for 30 days (currencies change rarely)."""

    def test_repeated_calls_hit_okama_once(self, monkeypatch):
        app = Flask(__name__)
        common.cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})
        with app.app_context():
            monkeypatch.delenv("TESTING", raising=False)
            calls = {"n": 0}

            def fake_symbols_in_namespace(ns, *args, **kwargs):
                calls["n"] += 1
                return _infl_frame(["USD", "EUR"])

            monkeypatch.setattr("okama.symbols_in_namespace", fake_symbols_in_namespace)

            assert inflation_mod.get_currency_list() == ["USD", "EUR"]
            assert inflation_mod.get_currency_list() == ["USD", "EUR"]
            assert calls["n"] == 1  # the second call is served from the cache

    def test_mock_currency_list_does_not_poison_real_list(self, monkeypatch):
        # Same trap as the symbol index (test_symbols_cache_isolation.py):
        # a TESTING=1 run must not write its mock currency list into the slot
        # the real app reads from.
        app = Flask(__name__)
        common.cache.init_app(app, config={"CACHE_TYPE": "SimpleCache"})
        with app.app_context():
            monkeypatch.setenv("TESTING", "1")
            monkeypatch.setattr(
                "okama.symbols_in_namespace", lambda ns, *a, **k: _infl_frame(["USD"])
            )
            assert inflation_mod.get_currency_list() == ["USD"]

            monkeypatch.delenv("TESTING", raising=False)
            monkeypatch.setattr(
                "okama.symbols_in_namespace", lambda ns, *a, **k: _infl_frame(["USD", "RUB"])
            )
            assert inflation_mod.get_currency_list() == ["USD", "RUB"]

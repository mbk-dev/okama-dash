"""resolve_url_currency: case-insensitive URL ccy validated against the currency list."""

import pytest

from common.inflation import resolve_url_currency

pytestmark = pytest.mark.unit

CURRENCIES = ["USD", "EUR", "RUB"]


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

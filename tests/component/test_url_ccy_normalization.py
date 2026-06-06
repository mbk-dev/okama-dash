"""Ccy from a shared URL must prefill the currency dropdown, never clear it.

dcc.Dropdown silently drops a value missing from its options on the client side,
so an unnormalized "usd" reached Submit as ccy=None and okama 404-ed on
"None.FX" (reported live on the EF page, 2026-06-06). Every page that prefills
the currency dropdown from the URL must normalize the value to uppercase and
validate it against the known currency list, falling back to the page default.
"""

import pytest

pytestmark = pytest.mark.component


def _walk(component):
    """Yield the component and all its descendants (components and strings)."""
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        yield from _walk(child)


def _dropdown_value(card, dropdown_id):
    for node in _walk(card):
        if getattr(node, "id", None) == dropdown_id:
            return node.value
    raise AssertionError(f"id {dropdown_id!r} not found")


class TestUrlCcyNormalization:
    def test_ef_lowercase_ccy_prefills_uppercase(self, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls

        card = card_controls(None, None, None, "usd", None)

        assert _dropdown_value(card, "ef-base-currency") == "USD"

    def test_ef_missing_ccy_falls_back_to_default(self, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls

        card = card_controls(None, None, None, None, None)

        assert _dropdown_value(card, "ef-base-currency") == "USD"

    def test_portfolio_lowercase_ccy_prefills_uppercase(self, mock_okama_symbols, null_cache):
        from pages.portfolio.cards_portfolio.portfolio_controls import card_controls

        card = card_controls(
            tickers=None,
            weights=None,
            first_date=None,
            last_date=None,
            ccy="usd",
            rebal=None,
            initial_amount=None,
            cashflow=None,
            discount_rate=None,
            symbol=None,
        )

        assert _dropdown_value(card, "pf-base-currency") == "USD"

    def test_compare_lowercase_ccy_prefills_uppercase(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import card_controls

        card = card_controls(None, None, None, "rub")

        assert _dropdown_value(card, "al-base-currency") == "RUB"

    def test_benchmark_lowercase_ccy_prefills_uppercase(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark.benchmark_controls import benchmark_card_controls

        card = benchmark_card_controls(None, None, None, None, "eur")

        assert _dropdown_value(card, "benchmark-base-currency") == "EUR"

    def test_ef_unknown_ccy_falls_back_to_default(self, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls

        card = card_controls(None, None, None, "xyz", None)

        assert _dropdown_value(card, "ef-base-currency") == "USD"

    def test_benchmark_unknown_ccy_falls_back_to_default(self, mock_okama_symbols, null_cache):
        from common import settings
        from pages.benchmark.cards_benchmark.benchmark_controls import benchmark_card_controls

        card = benchmark_card_controls(None, None, None, None, "xyz")

        assert _dropdown_value(card, "benchmark-base-currency") == settings.default_currency

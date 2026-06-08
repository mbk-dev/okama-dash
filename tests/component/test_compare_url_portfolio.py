"""Compare page accepts the pf_* URL portfolio group (issue #23).

The portfolio arrives as its own param group, shows up as a synthetic chip in
the tickers MultiSelect, joins the AssetList on Submit, and round-trips
through the page's copy-link.
"""

import pytest

pytestmark = pytest.mark.component

PF_DEF = {
    "tickers": ["AAPL.US", "MSFT.US"],
    "weights": [60.0, 40.0],
    "rebal": "year",
    "symbol": "MyPF.PF",
}


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        yield from _walk(child)


def _find(node, component_id):
    for item in _walk(node):
        if getattr(item, "id", None) == component_id:
            return item
    raise AssertionError(f"id {component_id!r} not found")


class TestCompareLayoutPrefill:
    def test_store_and_chip_prefilled(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60,40", pf_rebal="year", pf_symbol="MyPF")

        assert _find(page, "al-url-portfolio").data == PF_DEF
        select = _find(page, "al-symbols-list")
        assert "MyPF.PF" in select.value
        assert {"value": "MyPF.PF", "label": "MyPF.PF"} in select.data

    def test_chip_coexists_with_page_tickers(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(tickers="GOOG.US", pf_tickers="AAPL.US,MSFT.US", pf_weights="60,40")

        select = _find(page, "al-symbols-list")
        assert select.value == ["PORTFOLIO.PF", "GOOG.US"]

    def test_broken_group_renders_no_chip(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60")  # length mismatch

        assert _find(page, "al-url-portfolio").data is None
        select = _find(page, "al-symbols-list")
        assert select.value == []

    def test_plain_link_has_store_with_none(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(tickers="AAPL.US,MSFT.US")

        assert _find(page, "al-url-portfolio").data is None

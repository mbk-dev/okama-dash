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


def _find_by_id(component, component_id):
    for node in _walk(component):
        if getattr(node, "id", None) == component_id:
            return node
    raise AssertionError(f"id {component_id!r} not found in layout")


class TestParseUrlPortfolio:
    def test_valid_section_parsed(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        result = _parse_url_portfolio(["SPY.US", "BND.US"], "60,40", "MyPF")

        assert result == {
            "tickers": ["SPY.US", "BND.US"],
            "weights": [60.0, 40.0],
            "symbol": "MyPF",
        }

    def test_none_when_weights_missing(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], None, None) is None

    def test_none_when_weights_unparseable(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,abc", None) is None

    def test_none_when_count_mismatch(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,30,10", None) is None

    def test_none_when_sum_not_100(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,30", None) is None

    def test_none_when_weights_contain_empty_field(self):
        # "60," parses to [60.0, nan]; the NaN sum must not slip through the
        # tolerance check (NaN comparisons are False both ways).
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,", None) is None


class TestLayoutStore:
    def test_layout_puts_portfolio_section_into_store(self, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.frontier import layout

        page = layout(tickers="SPY.US,BND.US", weights="60,40", symbol="MyPF")

        store = _find_by_id(page, "ef-url-portfolio")
        assert store.data == {
            "tickers": ["SPY.US", "BND.US"],
            "weights": [60.0, 40.0],
            "symbol": "MyPF",
        }

    def test_layout_store_empty_without_weights(self, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.frontier import layout

        page = layout(tickers="SPY.US,BND.US")

        store = _find_by_id(page, "ef-url-portfolio")
        assert store.data is None

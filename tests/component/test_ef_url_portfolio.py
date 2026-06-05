from unittest.mock import MagicMock, patch

import pandas as pd
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


class TestGetPortfolioPoint:
    def _mock_pf(self):
        pf = MagicMock()
        pf.symbol = "portfolio_1.PF"
        pf.risk_annual = pd.Series([0.08, 0.11], index=["2023-12", "2024-12"])
        pf.get_cagr.return_value = pd.DataFrame(
            {"portfolio_1.PF": [0.07, 0.085]}, index=["2023-12", "2024-12"]
        )
        return pf

    def test_returns_percent_risk_and_cagr(self):
        from pages.efficient_frontier.ef_cache import get_portfolio_point

        pf = self._mock_pf()
        with patch(
            "pages.efficient_frontier.ef_cache.get_or_create",
            return_value=(pf, "key.pkl"),
        ) as mock_goc:
            point = get_portfolio_point(
                symbols=["SPY.US", "BND.US"],
                weights_percent=[60.0, 40.0],
                ccy="USD",
                first_date="2015-01",
                last_date="2024-12",
                rebalancing_period="year",
            )

        assert point == {"risk": pytest.approx(11.0), "cagr": pytest.approx(8.5)}
        kwargs = mock_goc.call_args.kwargs
        assert kwargs["obj_type"] == "portfolio"
        assert kwargs["cache_key_params"]["weights"] == [0.6, 0.4]
        assert kwargs["cache_key_params"]["purpose"] == "ef_point"

    def test_constructor_builds_portfolio_with_fraction_weights(self):
        from pages.efficient_frontier import ef_cache

        pf = self._mock_pf()
        captured = {}

        def fake_get_or_create(*, obj_type, constructor_fn, cache_key_params, ttl_seconds):
            captured["constructor"] = constructor_fn
            return pf, "key.pkl"

        with (
            patch(
                "pages.efficient_frontier.ef_cache.get_or_create",
                side_effect=fake_get_or_create,
            ),
            patch(
                "pages.efficient_frontier.ef_cache.ok.Portfolio", return_value=pf
            ) as mock_pf_cls,
            patch("pages.efficient_frontier.ef_cache.ok.Rebalance") as mock_rebal,
        ):
            ef_cache.get_portfolio_point(
                symbols=["SPY.US", "BND.US"],
                weights_percent=[60.0, 40.0],
                ccy="USD",
                first_date="2015-01",
                last_date="2024-12",
                rebalancing_period="year",
            )
            captured["constructor"]()

        mock_rebal.assert_called_once_with(period="year")
        call_kwargs = mock_pf_cls.call_args.kwargs
        assert call_kwargs["weights"] == [0.6, 0.4]
        assert call_kwargs["inflation"] is False
        assert call_kwargs["ccy"] == "USD"

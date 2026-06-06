from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go
import pytest

pytestmark = pytest.mark.component

FRONTIER_MODULE = "pages.efficient_frontier.frontier"


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
        pf.get_cagr.return_value = pd.DataFrame({"portfolio_1.PF": [0.07, 0.085]}, index=["2023-12", "2024-12"])
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
            patch("pages.efficient_frontier.ef_cache.ok.Portfolio", return_value=pf) as mock_pf_cls,
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


def _ef_frame_percent():
    # Mirrors what update_ef_cards passes: ef_points already multiplied by 100.
    return pd.DataFrame(
        {
            "Risk": [5.0, 20.0],
            "CAGR": [4.0, 11.0],
            "SPY.US": [100.0, 0.0],
            "BND.US": [0.0, 100.0],
        }
    )


def _ef_object_mock():
    ef_object = MagicMock()
    ef_object.symbols = ["SPY.US", "BND.US"]
    ef_object.get_cagr.return_value = pd.Series([0.08, 0.04], index=["SPY.US", "BND.US"])
    ef_object.risk_annual = pd.DataFrame({"SPY.US": [0.18], "BND.US": [0.06]})
    return ef_object


def _ef_options(url_portfolio=None):
    options = {
        "plot_type": ["Frontier"],
        "return_type": "Geometric",
        "mdp": "Off",
        "cml": "Off",
        "rf_rate": 0.0,
        "n_monte_carlo": 0,
        "grid_step": None,
    }
    if url_portfolio is not None:
        options["url_portfolio"] = url_portfolio
    return options


class TestPrepareEfUrlPortfolioTrace:
    PAYLOAD = {"risk": 11.0, "cagr": 8.5, "weights": [60.0, 40.0], "label": "MyPF"}

    def test_star_trace_added_with_label_and_coordinates(self):
        from pages.efficient_frontier.prepare_ef_plot import prepare_ef

        fig = prepare_ef(_ef_frame_percent(), _ef_object_mock(), _ef_options(self.PAYLOAD))

        pf_traces = [t for t in fig.data if t.name == "MyPF"]
        assert len(pf_traces) == 1
        assert list(pf_traces[0].x) == [11.0]
        assert list(pf_traces[0].y) == [8.5]
        assert pf_traces[0].marker.symbol == "star"

    def test_trace_customdata_serializes_as_json_list(self):
        # plotly>=6 drops numpy customdata from clickData (plotly/plotly.py#5119);
        # the weights must serialize as a JSON array to reach display_click_data.
        import json

        import plotly.io as pio

        from pages.efficient_frontier.prepare_ef_plot import prepare_ef

        fig = prepare_ef(_ef_frame_percent(), _ef_object_mock(), _ef_options(self.PAYLOAD))

        serialized = json.loads(pio.to_json(fig))["data"]
        pf_trace = next(t for t in serialized if t.get("name") == "MyPF")
        assert isinstance(pf_trace["customdata"], list)
        assert pf_trace["customdata"][0] == [60.0, 40.0]

    def test_no_trace_without_payload(self):
        from pages.efficient_frontier.prepare_ef_plot import prepare_ef

        fig = prepare_ef(_ef_frame_percent(), _ef_object_mock(), _ef_options())

        assert "MyPF" not in [t.name for t in fig.data]


def _make_mock_ef_object():
    import numpy as np

    ef = MagicMock()
    ef.symbols = ["AAPL.US", "MSFT.US"]
    ef.currency = "USD"
    ef.first_date = pd.Timestamp("2020-01-01")
    ef.last_date = pd.Timestamp("2024-12-01")
    ef.ef_points = pd.DataFrame(
        {
            "Mean return": np.linspace(0.04, 0.12, 10),
            "CAGR": np.linspace(0.035, 0.11, 10),
            "Risk": np.linspace(0.05, 0.20, 10),
            "AAPL.US": np.linspace(0.0, 1.0, 10),
            "MSFT.US": np.linspace(1.0, 0.0, 10),
        }
    )
    return ef


def _call_update_ef_cards(url_portfolio, captured, point_patch):
    from pages.efficient_frontier.frontier import update_ef_cards

    def fake_prepare_ef(ef, ef_object, ef_options, ef_cache_key=None):
        captured["ef_options"] = ef_options
        return go.Figure()

    with (
        patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(_make_mock_ef_object(), "t.pkl")),
        patch(f"{FRONTIER_MODULE}.prepare_ef", side_effect=fake_prepare_ef),
        patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=go.Figure()),
        patch(f"{FRONTIER_MODULE}.get_portfolio_point", **point_patch) as mock_point,
    ):
        result = update_ef_cards(
            screen=None,
            n_clicks=1,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            rebalancing_period="month",
            plot_option="Frontier",
            mdp_option="Off",
            cml_option="Off",
            rf_rate=0.0,
            n_monte_carlo=0,
            sim_mode="Off",
            grid_step_value="Auto",
            url_portfolio=url_portfolio,
        )
    return result, mock_point


class TestUpdateEfCardsUrlPortfolio:
    STORE = {"tickers": ["AAPL.US", "MSFT.US"], "weights": [60.0, 40.0], "symbol": "MyPF"}

    def test_payload_passed_when_tickers_match(self):
        captured = {}
        _call_update_ef_cards(self.STORE, captured, {"return_value": {"risk": 11.0, "cagr": 8.5}})

        assert captured["ef_options"]["url_portfolio"] == {
            "risk": 11.0,
            "cagr": 8.5,
            "weights": [60.0, 40.0],
            "label": "MyPF",
        }

    def test_payload_none_when_tickers_differ(self):
        captured = {}
        store = {"tickers": ["SPY.US", "BND.US"], "weights": [60.0, 40.0], "symbol": "MyPF"}
        _, mock_point = _call_update_ef_cards(store, captured, {"return_value": {"risk": 11.0, "cagr": 8.5}})

        assert captured["ef_options"]["url_portfolio"] is None
        mock_point.assert_not_called()

    def test_point_failure_does_not_break_figure(self):
        captured = {}
        result, _ = _call_update_ef_cards(self.STORE, captured, {"side_effect": ValueError("okama failed")})

        # The frontier still renders through the normal path: prepare_ef was
        # reached and the file name is returned (not the error-annotation path).
        assert captured["ef_options"]["url_portfolio"] is None
        assert result[4] == "t.pkl"

    def test_default_label_when_symbol_missing(self):
        captured = {}
        store = {"tickers": ["AAPL.US", "MSFT.US"], "weights": [60.0, 40.0], "symbol": None}
        _call_update_ef_cards(store, captured, {"return_value": {"risk": 11.0, "cagr": 8.5}})

        assert captured["ef_options"]["url_portfolio"]["label"] == "PORTFOLIO"

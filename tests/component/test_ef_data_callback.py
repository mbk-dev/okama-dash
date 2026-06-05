from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

import dash.exceptions

from common import settings as _settings

pytestmark = pytest.mark.component

FRONTIER_MODULE = "pages.efficient_frontier.frontier"


def _make_mock_ef_object():
    ef = MagicMock()
    ef.symbols = ["AAPL.US", "MSFT.US"]
    ef.currency = "USD"
    ef.first_date = pd.Timestamp("2020-01-01")
    ef.last_date = pd.Timestamp("2024-12-01")
    ef_points = pd.DataFrame({
        "Mean return": np.linspace(0.04, 0.12, 10),
        "CAGR": np.linspace(0.035, 0.11, 10),
        "Risk": np.linspace(0.05, 0.20, 10),
        "AAPL.US": np.linspace(0.0, 1.0, 10),
        "MSFT.US": np.linspace(1.0, 0.0, 10),
    })
    ef.ef_points = ef_points
    return ef


class TestUpdateEfCards:
    def test_returns_two_figures_and_file_name(self):
        from pages.efficient_frontier.frontier import update_ef_cards

        mock_ef = _make_mock_ef_object()
        fig1 = go.Figure()
        fig2 = go.Figure()

        with (
            patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(mock_ef, "test.pkl")),
            patch(f"{FRONTIER_MODULE}.prepare_ef", return_value=fig1),
            patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=fig2),
        ):
            r_fig1, r_fig2, config1, config2, file_name = update_ef_cards(
                screen=None, n_clicks=1,
                selected_symbols=["AAPL.US", "MSFT.US"],
                ccy="USD", fd_value="2020-01", ld_value="2024-12",
                rebalancing_period="month", plot_option="ef",
                mean_type_option="Arithmetic", mdp_option="Off",
                cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
                sim_mode="Off", grid_step_value="Auto",
            )

        assert isinstance(r_fig1, go.Figure)
        assert isinstance(r_fig2, go.Figure)
        assert file_name == "test.pkl"

    def test_empty_symbols_raises_prevent_update(self):
        from pages.efficient_frontier.frontier import update_ef_cards

        with pytest.raises(dash.exceptions.PreventUpdate):
            update_ef_cards(
                screen=None, n_clicks=1,
                selected_symbols=[],
                ccy="USD", fd_value="2020-01", ld_value="2024-12",
                rebalancing_period="month", plot_option="ef",
                mean_type_option="Arithmetic", mdp_option="Off",
                cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
                sim_mode="Off", grid_step_value="Auto",
            )

    def test_exception_returns_error_figure(self):
        from pages.efficient_frontier.frontier import update_ef_cards

        with patch(
            f"{FRONTIER_MODULE}.get_or_create_ef_object",
            side_effect=ValueError("EF failed"),
        ):
            fig1, fig2, c1, c2, fname = update_ef_cards(
                screen=None, n_clicks=1,
                selected_symbols=["AAPL.US"],
                ccy="USD", fd_value="2020-01", ld_value="2024-12",
                rebalancing_period="month", plot_option="ef",
                mean_type_option="Arithmetic", mdp_option="Off",
                cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
                sim_mode="Off", grid_step_value="Auto",
            )

        assert isinstance(fig1, go.Figure)
        assert fname is None

    def test_ef_points_multiplied_by_100(self):
        from pages.efficient_frontier.frontier import update_ef_cards

        mock_ef = _make_mock_ef_object()

        with (
            patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(mock_ef, "t.pkl")),
            patch(f"{FRONTIER_MODULE}.prepare_ef") as mock_prep_ef,
            patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=go.Figure()),
        ):
            mock_prep_ef.return_value = go.Figure()
            update_ef_cards(
                screen=None, n_clicks=1,
                selected_symbols=["AAPL.US", "MSFT.US"],
                ccy="USD", fd_value="2020-01", ld_value="2024-12",
                rebalancing_period="month", plot_option="ef",
                mean_type_option="Arithmetic", mdp_option="Off",
                cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
                sim_mode="Off", grid_step_value="Auto",
            )

        ef_arg = mock_prep_ef.call_args[0][0]
        assert ef_arg["Risk"].iloc[0] == pytest.approx(5.0, abs=0.1)

    def test_mobile_compacts_figure(self):
        from pages.efficient_frontier.frontier import update_ef_cards

        mock_ef = _make_mock_ef_object()

        with (
            patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(mock_ef, "t.pkl")),
            patch(f"{FRONTIER_MODULE}.prepare_ef", return_value=go.Figure()),
            patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=go.Figure()),
            patch(f"{FRONTIER_MODULE}.compact_ef_for_small_screens") as mock_compact,
        ):
            mock_compact.return_value = go.Figure()
            update_ef_cards(
                screen={"in_width": 375, "in_height": 812}, n_clicks=1,
                selected_symbols=["AAPL.US", "MSFT.US"],
                ccy="USD", fd_value="2020-01", ld_value="2024-12",
                rebalancing_period="month", plot_option="ef",
                mean_type_option="Arithmetic", mdp_option="Off",
                cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
                sim_mode="Off", grid_step_value="Auto",
            )

        mock_compact.assert_called_once()


def test_grid_trace_added_when_grid_step_set():
    from pages.efficient_frontier.prepare_ef_plot import _prepare_single_ef

    ef = pd.DataFrame({
        "Risk": [0.05, 0.10],
        "CAGR": [0.04, 0.08],
        "A.US": [1.0, 0.0],
        "B.US": [0.0, 1.0],
    })
    ef_object = MagicMock()
    ef_object.symbols = ["A.US", "B.US"]
    ef_object.get_grid_portfolios.return_value = pd.DataFrame({
        "Risk": [0.06, 0.07, 0.08],
        "CAGR": [0.05, 0.06, 0.07],
        "A.US": [0.5, 0.3, 0.2],
        "B.US": [0.5, 0.7, 0.8],
    })
    ef_options = {
        "return_type": "Geometric",
        "mdp": "Off",
        "cml": "Off",
        "n_monte_carlo": 0,
        "grid_step": 0.5,
    }

    fig = _prepare_single_ef(
        ef, ef_object, ef_options, fig=go.Figure(), include_assets=False, ef_cache_key=None
    )

    grid_traces = [trace for trace in fig.data if trace.name == "Grid portfolios"]
    assert len(grid_traces) == 1
    assert list(grid_traces[0].x) == pytest.approx([6.0, 7.0, 8.0])   # Risk * 100
    ef_object.get_grid_portfolios.assert_called_once_with(
        step=0.5, max_points=_settings.GRID_POINT_BUDGET
    )


def test_customdata_serializes_as_json_lists_for_clickdata():
    # Regression: plotly>=6 serializes numpy arrays as base64 typed-array objects
    # ({"dtype": ..., "bdata": ...}), which never reach clickData["points"][0]["customdata"]
    # in the browser (plotly/plotly.py#5119) — display_click_data then shows
    # "Weights: unavailable". Every trace must carry customdata as plain lists so it
    # serializes to a JSON array and survives into the click event.
    import json

    import plotly.io as pio

    from pages.efficient_frontier.prepare_ef_plot import _prepare_single_ef

    ef = pd.DataFrame({
        "Risk": [0.05, 0.10],
        "CAGR": [0.04, 0.08],
        "A.US": [1.0, 0.0],
        "B.US": [0.0, 1.0],
    })
    ef_object = MagicMock()
    ef_object.symbols = ["A.US", "B.US"]
    ef_object.get_cagr.return_value = pd.Series([0.08, 0.10], index=["A.US", "B.US"])
    ef_object.risk_annual = pd.DataFrame({"A.US": [0.15], "B.US": [0.20]})
    ef_options = {
        "return_type": "Geometric",
        "mdp": "Off",
        "cml": "Off",
        "n_monte_carlo": 0,
        "grid_step": None,
    }

    fig = _prepare_single_ef(
        ef, ef_object, ef_options, fig=go.Figure(), include_assets=True, ef_cache_key=None
    )

    serialized_traces = json.loads(pio.to_json(fig))["data"]
    for trace in serialized_traces:
        if "customdata" in trace:
            assert isinstance(trace["customdata"], list), (
                f"customdata of trace {trace.get('name')!r} serialized as"
                f" {type(trace['customdata']).__name__} — clickData would lose it"
            )


def test_grid_mode_passes_resolved_step_to_prepare_ef():
    from pages.efficient_frontier.frontier import update_ef_cards

    mock_ef = _make_mock_ef_object()
    captured = {}

    def fake_prepare_ef(ef, ef_object, ef_options, ef_cache_key=None):
        captured["ef_options"] = ef_options
        return go.Figure()

    with (
        patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(mock_ef, "test.pkl")),
        patch(f"{FRONTIER_MODULE}.prepare_ef", side_effect=fake_prepare_ef),
        patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=go.Figure()),
    ):
        update_ef_cards(
            screen=None, n_clicks=1,
            selected_symbols=["A.US", "B.US", "C.US", "D.US", "E.US", "F.US"],
            ccy="USD", fd_value="2020-01", ld_value="2024-12",
            rebalancing_period="month", plot_option="Frontier",
            mean_type_option="Geometric", mdp_option="Off",
            cml_option="Off", rf_rate=0.0, n_monte_carlo=0,
            sim_mode="Grid", grid_step_value="Auto",
        )

    assert captured["ef_options"]["grid_step"] == 0.10   # 6 assets -> 10%
    assert captured["ef_options"]["n_monte_carlo"] == 0


def test_monte_carlo_mode_passes_n_and_no_grid_step():
    from pages.efficient_frontier.frontier import update_ef_cards

    mock_ef = _make_mock_ef_object()
    captured = {}

    def fake_prepare_ef(ef, ef_object, ef_options, ef_cache_key=None):
        captured["ef_options"] = ef_options
        return go.Figure()

    with (
        patch(f"{FRONTIER_MODULE}.get_or_create_ef_object", return_value=(mock_ef, "test.pkl")),
        patch(f"{FRONTIER_MODULE}.prepare_ef", side_effect=fake_prepare_ef),
        patch(f"{FRONTIER_MODULE}.prepare_transition_map", return_value=go.Figure()),
    ):
        update_ef_cards(
            screen=None, n_clicks=1,
            selected_symbols=["A.US", "B.US"],
            ccy="USD", fd_value="2020-01", ld_value="2024-12",
            rebalancing_period="month", plot_option="Frontier",
            mean_type_option="Geometric", mdp_option="Off",
            cml_option="Off", rf_rate=0.0, n_monte_carlo=100,
            sim_mode="Monte Carlo", grid_step_value="Auto",
        )

    assert captured["ef_options"]["grid_step"] is None
    assert captured["ef_options"]["n_monte_carlo"] == 100

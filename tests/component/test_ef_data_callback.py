from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

import dash.exceptions

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
            )

        mock_compact.assert_called_once()

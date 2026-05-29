from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import dash_table

from tests.mocks.okama_mock import make_mock_portfolio

pytestmark = pytest.mark.component

PF_MODULE = "pages.portfolio.portfolio"


def _default_args():
    return {
        "screen": None, "log_on": False,
        "assets": ["AAPL.US", "MSFT.US"], "weights": [50, 50],
        "ccy": "USD", "rebalancing_period": "month",
        "rebal_abs_deviation": None, "rebal_rel_deviation": None,
        "fd_value": "2020-01", "ld_value": "2024-12",
        "initial_amount": 1000, "discount_rate": 0, "symbol": "TestPF",
        "cf_strategy": "indexation", "cf_frequency": "month",
        "cf_amount": 0, "cf_indexation": 0, "cf_percentage": 0,
        "vds_percentage": 0, "vds_min_withdrawal": 0, "vds_max_withdrawal": 0,
        "vds_adjust_minmax": True, "vds_floor": 0, "vds_ceiling": 0,
        "vds_adjust_fc": False, "vds_indexation": 0,
        "cwd_amount": 0, "cwd_indexation": 0, "cwd_thresholds": [], "cwd_reductions": [],
        "ts_dates": [], "ts_amounts": [],
        "plot_type": "wealth", "inflation_on": False, "rolling_window": 2,
        "n_monte_carlo": 0, "years_monte_carlo": 0,
        "distribution_monte_carlo": "norm", "show_backtest": "On",
    }


@pytest.fixture
def patched_pf_inner(tmp_path):
    mock_pf = make_mock_portfolio()
    mock_fig = go.Figure()
    mock_fig.add_scatter(x=[1, 2], y=[100, 110], name="TestPF.PF")
    empty_df = pd.DataFrame()

    def _run_constructor(obj_type, constructor_fn, cache_key_params, ttl_seconds):
        constructor_fn()
        return mock_pf, "test.pkl"

    with (
        patch(f"{PF_MODULE}.get_or_create", side_effect=_run_constructor),
        patch(f"{PF_MODULE}.ok.Portfolio", return_value=mock_pf),
        patch(f"{PF_MODULE}.ok.Rebalance", return_value=MagicMock()),
        patch(f"{PF_MODULE}.ok.IndexationStrategy", return_value=MagicMock()),
        patch(f"{PF_MODULE}.get_pf_figure", return_value=(mock_fig, empty_df, empty_df, empty_df)),
        patch(f"{PF_MODULE}.get_pf_statistics_table", return_value=dash_table.DataTable(data=[{"a": 1}])),
    ):
        yield mock_pf


class TestUpdateGrafPortfolioInner:
    def test_returns_figure_and_tables(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        result = _update_graf_portfolio_inner(**_default_args())
        fig, config, stats, forecast_surv, forecast_wealth, json_data = result

        assert isinstance(fig, go.Figure)
        assert isinstance(config, dict)
        assert json_data is not None

    def test_wealth_plot_sets_y_title(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        result = _update_graf_portfolio_inner(**_default_args())
        fig = result[0]
        assert fig.layout.yaxis.title.text == "Wealth Indexes"

    def test_cagr_plot_sets_y_title(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["plot_type"] = "cagr"
        fig = _update_graf_portfolio_inner(**args)[0]
        assert fig.layout.yaxis.title.text == "CAGR"

    def test_drawdowns_plot_sets_y_title(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["plot_type"] = "drawdowns"
        fig = _update_graf_portfolio_inner(**args)[0]
        assert fig.layout.yaxis.title.text == "Drawdowns"

    def test_no_monte_carlo_returns_empty_forecast_tables(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        result = _update_graf_portfolio_inner(**_default_args())
        forecast_surv = result[3]
        forecast_wealth = result[4]
        assert isinstance(forecast_surv, dash_table.DataTable)
        assert isinstance(forecast_wealth, dash_table.DataTable)

    def test_weights_divided_by_100(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        with patch(f"{PF_MODULE}.ok.Portfolio") as mock_cls:
            mock_cls.return_value = patched_pf_inner
            _update_graf_portfolio_inner(**_default_args())
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["weights"] == [0.5, 0.5]

    def test_symbol_gets_pf_suffix(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        with patch(f"{PF_MODULE}.ok.Portfolio") as mock_cls:
            mock_cls.return_value = patched_pf_inner
            _update_graf_portfolio_inner(**_default_args())
            assert mock_cls.call_args[1]["symbol"] == "TestPF.PF"


class TestUpdateGrafPortfolioOuter:
    def test_exception_opens_toast_with_message(self):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,

            patch(f"{PF_MODULE}._update_graf_portfolio_inner", side_effect=ValueError("boom")),
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(), n_clicks=1,
            )

        toast_is_open = result[6]
        toast_children = result[7]
        assert toast_is_open is True
        assert "boom" in str(toast_children)

    def test_exception_hides_graph_and_stats_rows(self):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,

            patch(f"{PF_MODULE}._update_graf_portfolio_inner", side_effect=ValueError("boom")),
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(), n_clicks=1,
            )

        graf_row_style = result[8]
        stats_row_style = result[9]
        assert graf_row_style == {"display": "none"}
        assert stats_row_style == {"display": "none"}

    def test_success_closes_toast_and_shows_rows(self, patched_pf_inner):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,

        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(), n_clicks=1,
            )

        toast_is_open = result[6]
        graf_row_style = result[8]
        stats_row_style = result[9]
        assert toast_is_open is False
        assert graf_row_style is None
        assert stats_row_style is None

    def test_log_scale_toggle_no_update_toast_and_rows(self):
        import dash
        from pages.portfolio.portfolio import update_graf_portfolio

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-logarithmic-scale-switch"
            args = _default_args()
            args["log_on"] = True
            result = update_graf_portfolio(
                **args, n_clicks=1,
            )

        assert result[6] is dash.no_update
        assert result[7] is dash.no_update
        assert result[8] is dash.no_update
        assert result[9] is dash.no_update

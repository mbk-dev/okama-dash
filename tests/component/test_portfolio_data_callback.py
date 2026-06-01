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

    def test_annual_return_plot_sets_y_title(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["plot_type"] = "annual_return"
        fig = _update_graf_portfolio_inner(**args)[0]
        assert fig.layout.yaxis.title.text == "Annual Return, %"

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

    def test_discount_rate_wired_to_dcf_as_decimal(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["discount_rate"] = 10  # entered as percent
        _update_graf_portfolio_inner(**args)
        assert patched_pf_inner.dcf.discount_rate == 0.10

    def test_empty_discount_rate_passed_as_none(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["discount_rate"] = None
        _update_graf_portfolio_inner(**args)
        assert patched_pf_inner.dcf.discount_rate is None


class TestGetPfFigureAnnualReturn:
    def test_annual_return_renders_bar_chart(self):
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, df_backtest, df_forecast, df_data = get_pf_figure(
            pf, plot_type="annual_return", inflation_on=False, rolling_window=2,
            n_monte_carlo=0, years_monte_carlo=0, distribution_monte_carlo="norm",
            show_backtest="no", log_scale=False, cf_strategy="indexation",
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        assert all(trace.type == "bar" for trace in fig.data)
        pf.annual_return_ts.assert_called_once()
        assert not df_data.empty

    def test_annual_return_uses_cagr_return_type_and_annotates(self):
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, *_ = get_pf_figure(
            pf, plot_type="annual_return", inflation_on=False, rolling_window=2,
            n_monte_carlo=0, years_monte_carlo=0, distribution_monte_carlo="norm",
            show_backtest="no", log_scale=False, cf_strategy="indexation",
        )
        pf.annual_return_ts.assert_called_once_with(return_type="cagr")
        annotation_texts = [a.text for a in fig.layout.annotations]
        assert any("CAGR" in t for t in annotation_texts)


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

    def test_exception_returns_no_row_styles(self):
        # Row visibility moved to its own callback, so the heavy callback no
        # longer carries the two trailing row-style outputs.
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,

            patch(f"{PF_MODULE}._update_graf_portfolio_inner", side_effect=ValueError("boom")),
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(), n_clicks=1,
            )

        assert len(result) == 8

    def test_success_closes_toast(self, patched_pf_inner):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,

        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(), n_clicks=1,
            )

        assert result[6] is False
        assert len(result) == 8

    def test_log_scale_toggle_no_update_toast(self):
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


class TestShowGrafAndStatisticsRows:
    # Row visibility lives in its own fast callback (like compare/benchmark/EF)
    # so the dcc.Loading spinner is visible while the slow chart callback runs.
    def test_reveals_both_rows_on_submit(self):
        from pages.portfolio.portfolio import show_graf_and_statistics_rows

        graf_style, stats_style = show_graf_and_statistics_rows(1, {"display": "none"})

        assert graf_style is None
        assert stats_style is None

    def test_keeps_rows_hidden_before_submit(self):
        from pages.portfolio.portfolio import show_graf_and_statistics_rows

        graf_style, stats_style = show_graf_and_statistics_rows(0, {"display": "none"})

        assert graf_style == {"display": "none"}
        assert stats_style == {"display": "none"}

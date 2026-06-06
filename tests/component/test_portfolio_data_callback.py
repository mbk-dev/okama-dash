from unittest.mock import MagicMock, patch

import dash_ag_grid as dag
import pandas as pd
import plotly.graph_objects as go
import pytest

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
        patch(f"{PF_MODULE}.get_pf_statistics_table", return_value=dag.AgGrid(rowData=[{"a": 1}])),
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

    def test_cumulative_return_plot_sets_y_title(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        args = _default_args()
        args["plot_type"] = "cumulative_return"
        fig = _update_graf_portfolio_inner(**args)[0]
        assert fig.layout.yaxis.title.text == "Cumulative Return"

    def test_no_monte_carlo_returns_empty_forecast_tables(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        result = _update_graf_portfolio_inner(**_default_args())
        forecast_surv = result[3]
        forecast_wealth = result[4]
        assert isinstance(forecast_surv, dag.AgGrid)
        assert isinstance(forecast_wealth, dag.AgGrid)

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


class TestForecastStatisticsTablesCompact:
    # On small screens (in_width < 800) the two-pane Survival/Wealth statistics
    # tables reflow into a single column of pairs so every cell stays readable.
    PERCENTILE_LABELS = [
        "1st percentile", "5th percentile", "25th percentile", "50th percentile",
        "75th percentile", "95th percentile", "99th percentile",
    ]

    @staticmethod
    def _pf_with_mc_stats():
        pf = make_mock_portfolio()
        pf.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
        wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
        wealth_pv = wealth_fv / 2
        pf.dcf.monte_carlo_wealth = MagicMock(
            side_effect=lambda discounting="fv": wealth_fv if discounting == "fv" else wealth_pv
        )
        return pf

    def test_survival_compact_stacks_pairs_in_single_column(self):
        from pages.portfolio.portfolio import get_forecast_survival_statistics_table

        pf = self._pf_with_mc_stats()
        result = get_forecast_survival_statistics_table(
            pd.DataFrame({"x": [1]}), pd.DataFrame(), pf, compact=True
        )
        grid = result.children[1]
        assert [row["1"] for row in grid.rowData] == self.PERCENTILE_LABELS + ["Min", "Max", "Mean", "Std"]
        assert all(set(row) == {"1", "2"} for row in grid.rowData)
        assert len(grid.columnDefs) == 2

    def test_survival_desktop_keeps_two_pane_layout(self):
        from pages.portfolio.portfolio import get_forecast_survival_statistics_table

        pf = self._pf_with_mc_stats()
        result = get_forecast_survival_statistics_table(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf)
        grid = result.children[1]
        assert len(grid.rowData) == 7
        assert all(set(row) == {"1", "2", "3", "4"} for row in grid.rowData)
        assert len(grid.columnDefs) == 4

    def test_wealth_compact_stacks_pairs_with_fv_pv_columns(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_table

        pf = self._pf_with_mc_stats()
        result = get_forecast_wealth_statistics_table(pf, compact=True)
        grid = result.children[1]
        labels = [row["1"] for row in grid.rowData]
        assert labels == self.PERCENTILE_LABELS + ["Min", "Max", "Mean", "Std", "Discount rate"]
        assert all(set(row) == {"1", "2", "3"} for row in grid.rowData)
        assert [col["headerName"] for col in grid.columnDefs] == ["", "FV", "PV"]
        discount_row = grid.rowData[-1]
        assert discount_row["2"] is None
        assert discount_row["3"] == "5.00%"

    def test_wealth_desktop_keeps_two_pane_layout(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_table

        pf = self._pf_with_mc_stats()
        result = get_forecast_wealth_statistics_table(pf)
        grid = result.children[1]
        assert len(grid.rowData) == 7
        assert all(set(row) == {"1", "2", "3", "4", "5", "6"} for row in grid.rowData)
        assert len(grid.columnDefs) == 6

    def test_inner_builds_compact_tables_on_small_screen(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        patched_pf_inner.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
        wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
        patched_pf_inner.dcf.monte_carlo_wealth = MagicMock(
            side_effect=lambda discounting="fv": wealth_fv if discounting == "fv" else wealth_fv / 2
        )
        args = _default_args()
        args["screen"] = {"in_width": 375}
        args["n_monte_carlo"] = 2
        non_empty_forecast = pd.DataFrame({0: [1.0]})
        with patch(
            f"{PF_MODULE}.get_pf_figure",
            return_value=(go.Figure(), pd.DataFrame(), non_empty_forecast, pd.DataFrame()),
        ):
            result = _update_graf_portfolio_inner(**args)
        survival_grid = result[3].children[1]
        wealth_grid = result[4].children[1]
        assert len(survival_grid.rowData) == 11  # 7 percentiles + Min/Max/Mean/Std
        assert len(wealth_grid.rowData) == 12  # + Discount rate


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


class TestGetPfFigureWealthAnnotations:
    def test_wealth_plot_annotates_each_trace_with_balance_points(self):
        from common.chart_helpers import format_points
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, *_ = get_pf_figure(
            pf, plot_type="wealth", inflation_on=False, rolling_window=2,
            n_monte_carlo=0, years_monte_carlo=0, distribution_monte_carlo="norm",
            show_backtest="no", log_scale=False, cf_strategy="indexation",
        )
        wealth = pf.wealth_index_with_assets
        texts = [a.text for a in fig.layout.annotations if a.text]
        for value in wealth.iloc[-1]:
            assert format_points(value) in texts
        assert not any(t.endswith("%") for t in texts)


class TestGetPfFigureCumulativeReturn:
    def test_cumulative_return_plots_ts_with_percent_annotations(self):
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, df_backtest, df_forecast, df_data = get_pf_figure(
            pf, plot_type="cumulative_return", inflation_on=False, rolling_window=2,
            n_monte_carlo=0, years_monte_carlo=0, distribution_monte_carlo="norm",
            show_backtest="no", log_scale=False, cf_strategy="indexation",
        )
        assert fig.layout.title.text == "Portfolio Cumulative Return"
        cum = pf.get_cumulative_return(real=False)
        texts = [a.text for a in fig.layout.annotations if a.text]
        for percent_text in (cum.iloc[-1] * 100).map("{:,.2f}%".format):
            assert percent_text in texts
        assert df_backtest.empty and df_forecast.empty
        assert not df_data.empty


class TestStatisticsGridDotNotation:
    def test_pf_statistics_grid_suppresses_field_dot_notation(self):
        # Column names derived from okama contain dots (portfolio_XXXX.PF); without
        # suppressFieldDotNotation AG Grid treats them as nested paths and renders
        # the metric columns empty.
        from pages.portfolio.portfolio import get_pf_statistics_table

        grid = get_pf_statistics_table(make_mock_portfolio())
        assert grid.dashGridOptions.get("suppressFieldDotNotation") is True

    def test_pf_statistics_columns_use_guarded_percent_function(self):
        # Inline typeof-guards are not supported by the dash-ag-grid function-string
        # parser; columns must call the registered assets/dashAgGridFunctions.js helper.
        from pages.portfolio.portfolio import get_pf_statistics_table

        grid = get_pf_statistics_table(make_mock_portfolio())
        assert all(
            d["valueFormatter"]["function"] == "formatPercentGuarded(params.value)"
            for d in grid.columnDefs
        )


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


class TestMonteCarloForecastZeroTermination:
    # Each MC scenario line must end exactly at zero when the portfolio dies,
    # then break (NaN) — same convention as the backtest wealth line.
    @staticmethod
    def _portfolio_with_mc_forecast():
        dates = pd.period_range("2025-01", "2025-06", freq="M")
        raw = pd.DataFrame(
            {
                0: [1000.0, 500.0, -100.0, -200.0, -300.0, -400.0],
                1: [1000.0, 1100.0, 1200.0, 1300.0, 1400.0, 1500.0],
            },
            index=dates,
        )

        def mc_wealth(discounting="fv", include_negative_values=True):
            # Mirrors okama monte_carlo_wealth: with include_negative_values=False
            # the first non-positive value becomes 0 and the tail is zero-filled.
            if include_negative_values:
                return raw.copy()
            out = raw.copy()
            out.loc[out[0] <= 0, 0] = 0.0
            return out

        pf = make_mock_portfolio()
        pf.dcf.cashflow_parameters.initial_investment = 1000.0
        pf.dcf.monte_carlo_wealth = MagicMock(side_effect=mc_wealth)
        return pf, dates

    def test_dead_scenario_ends_with_single_zero_then_breaks(self):
        from pages.portfolio.portfolio import _get_wealth_data

        pf, dates = self._portfolio_with_mc_forecast()
        _, _, df_forecast, _ = _get_wealth_data(
            pf, has_cashflow=True, n_monte_carlo=2, show_backtest_bool=False,
            distribution_mc="norm", years_mc=5,
        )

        dead = df_forecast[0]
        assert dead.loc[dates[2]] == 0  # death point kept at exactly zero
        assert dead.loc[dates[3]:].isna().all()  # line breaks after death

    def test_surviving_scenario_keeps_all_values(self):
        from pages.portfolio.portfolio import _get_wealth_data

        pf, _ = self._portfolio_with_mc_forecast()
        _, _, df_forecast, _ = _get_wealth_data(
            pf, has_cashflow=True, n_monte_carlo=2, show_backtest_bool=False,
            distribution_mc="norm", years_mc=5,
        )

        alive = df_forecast[1]
        assert alive.notna().all()
        assert (alive > 0).all()

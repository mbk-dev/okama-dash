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
        "screen": None,
        "log_on": False,
        "assets": ["AAPL.US", "MSFT.US"],
        "weights": [50, 50],
        "ccy": "USD",
        "rebalancing_period": "month",
        "rebal_abs_deviation": None,
        "rebal_rel_deviation": None,
        "fd_value": "2020-01",
        "ld_value": "2024-12",
        "initial_amount": 1000,
        "discount_rate": 0,
        "symbol": "TestPF",
        "cf_strategy": "indexation",
        "cf_frequency": "month",
        "cf_amount": 0,
        "cf_indexation": 0,
        "cf_percentage": 0,
        "vds_percentage": 0,
        "vds_min_withdrawal": 0,
        "vds_max_withdrawal": 0,
        "vds_adjust_minmax": True,
        "vds_floor": 0,
        "vds_ceiling": 0,
        "vds_adjust_fc": False,
        "vds_indexation": 0,
        "cwd_amount": 0,
        "cwd_indexation": 0,
        "cwd_thresholds": [],
        "cwd_reductions": [],
        "ts_dates": [],
        "ts_amounts": [],
        "plot_type": "wealth",
        "inflation_on": False,
        "rolling_window": 2,
        "n_monte_carlo": 0,
        "years_monte_carlo": 0,
        "distribution_monte_carlo": "norm",
        "show_backtest": "On",
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
        fig, config, stats, forecast_surv, forecast_wealth, forecast_irr, json_data = result

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


def _pf_with_mc_stats():
    pf = make_mock_portfolio()
    pf.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
    wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
    wealth_pv = wealth_fv / 2
    pf.dcf.monte_carlo_wealth = MagicMock(
        side_effect=lambda discounting="fv", include_negative_values=True: (
            wealth_fv if discounting == "fv" else wealth_pv
        )
    )
    return pf


def _section_tabs(section):
    """dbc.Tabs of a tabbed MC statistics section (children: header row, tabs)."""
    return section.children[1]


def _section_grid(section):
    """Grid from the Table tab of a tabbed MC statistics section."""
    return _section_tabs(section).children[0].children


def _section_graph(section):
    """dcc.Graph from the Distribution tab of a tabbed MC statistics section."""
    return _section_tabs(section).children[1].children


class TestForecastStatisticsTablesCompact:
    # On small screens (in_width < 800) the two-pane Survival/Wealth statistics
    # tables reflow into a single column of pairs so every cell stays readable.
    PERCENTILE_LABELS = [
        "1st percentile",
        "5th percentile",
        "25th percentile",
        "50th percentile",
        "75th percentile",
        "95th percentile",
        "99th percentile",
    ]

    def test_survival_compact_stacks_pairs_in_single_column(self):
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        pf = _pf_with_mc_stats()
        result = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf, compact=True)
        grid = _section_grid(result)
        assert [row["1"] for row in grid.rowData] == self.PERCENTILE_LABELS + ["Min", "Max", "Mean", "Std"]
        assert all(set(row) == {"1", "2"} for row in grid.rowData)
        assert len(grid.columnDefs) == 2

    def test_survival_desktop_keeps_two_pane_layout(self):
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        pf = _pf_with_mc_stats()
        result = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf)
        grid = _section_grid(result)
        assert len(grid.rowData) == 7
        assert all(set(row) == {"1", "2", "3", "4"} for row in grid.rowData)
        assert len(grid.columnDefs) == 4

    def test_wealth_compact_stacks_pairs_with_fv_pv_columns(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_section

        pf = _pf_with_mc_stats()
        result = get_forecast_wealth_statistics_section(pf, compact=True)
        grid = _section_grid(result)
        labels = [row["1"] for row in grid.rowData]
        assert labels == self.PERCENTILE_LABELS + ["Min", "Max", "Mean", "Std", "Discount rate"]
        assert all(set(row) == {"1", "2", "3"} for row in grid.rowData)
        assert [col["headerName"] for col in grid.columnDefs] == ["", "FV", "PV"]
        discount_row = grid.rowData[-1]
        assert discount_row["2"] is None
        assert discount_row["3"] == "5.00%"

    def test_wealth_desktop_keeps_two_pane_layout(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_section

        pf = _pf_with_mc_stats()
        result = get_forecast_wealth_statistics_section(pf)
        grid = _section_grid(result)
        assert len(grid.rowData) == 7
        assert all(set(row) == {"1", "2", "3", "4", "5", "6"} for row in grid.rowData)
        assert len(grid.columnDefs) == 6


class TestMcStatisticsTabs:
    """Issue #18: Survival/Wealth MC sections are tabbed — Table + Distribution."""

    def test_survival_section_has_table_and_distribution_tabs(self):
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        result = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame(), _pf_with_mc_stats())

        tabs = _section_tabs(result)
        assert type(tabs).__name__ == "Tabs"
        assert [tab.label for tab in tabs.children] == ["Table", "Distribution"]
        assert tabs.active_tab == "table"

    def test_wealth_section_has_table_and_distribution_tabs(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_section

        result = get_forecast_wealth_statistics_section(_pf_with_mc_stats())

        tabs = _section_tabs(result)
        assert type(tabs).__name__ == "Tabs"
        assert [tab.label for tab in tabs.children] == ["Table", "Distribution"]

    def test_table_tabs_keep_the_export_grid_ids(self):
        from pages.portfolio.portfolio import (
            get_forecast_survival_statistics_section,
            get_forecast_wealth_statistics_section,
        )

        pf = _pf_with_mc_stats()
        survival = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf)
        wealth = get_forecast_wealth_statistics_section(pf)

        assert isinstance(_section_grid(survival), dag.AgGrid)
        assert _section_grid(survival).id == "pf-survival-statistics-grid"
        assert _section_grid(wealth).id == "pf-wealth-statistics-grid"

    def test_survival_histogram_plots_the_offset_series(self):
        # The chart must show the same series the table is computed from:
        # MC survival periods shifted by the backtest survival period.
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        pf = _pf_with_mc_stats()
        pf.dcf.survival_period_hist.return_value = 25.0
        result = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame({"y": [1]}), pf)

        figure = _section_graph(result).figure
        assert len(figure.data) == 1
        trace = figure.data[0]
        assert trace.type == "histogram"
        assert trace.histnorm == "probability"
        assert list(trace.x) == [45.0, 50.0, 55.0]

    def test_wealth_histogram_overlays_fv_and_pv(self):
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_section

        result = get_forecast_wealth_statistics_section(_pf_with_mc_stats())

        figure = _section_graph(result).figure
        assert figure.layout.barmode == "overlay"
        assert [trace.name for trace in figure.data] == ["FV", "PV"]
        assert list(figure.data[0].x) == [200.0, 250.0]
        assert list(figure.data[1].x) == [100.0, 125.0]

    def test_wealth_series_exclude_negative_balances(self):
        # A depleted portfolio balance is 0, never negative: both FV and PV
        # series must be fetched with include_negative_values=False (okama
        # replaces negatives with 0) — same flag the main MC chart uses.
        from pages.portfolio.portfolio import get_forecast_wealth_statistics_section

        pf = _pf_with_mc_stats()
        get_forecast_wealth_statistics_section(pf)

        calls = pf.dcf.monte_carlo_wealth.call_args_list
        assert calls, "monte_carlo_wealth was never called"
        assert all(call.kwargs.get("include_negative_values") is False for call in calls)

    def test_constant_survival_series_still_builds_a_figure(self):
        # All paths surviving the same period: bin width must not divide by zero.
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        pf = _pf_with_mc_stats()
        pf.dcf.monte_carlo_survival_period.return_value = pd.Series([25.0, 25.0, 25.0])
        result = get_forecast_survival_statistics_section(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf)

        figure = _section_graph(result).figure
        assert list(figure.data[0].x) == [25.0, 25.0, 25.0]

    def test_empty_forecast_renders_table_only(self):
        # Backtest-only branch has no MC series — nothing to plot, no tabs.
        from pages.portfolio.portfolio import get_forecast_survival_statistics_section

        pf = _pf_with_mc_stats()
        result = get_forecast_survival_statistics_section(pd.DataFrame(), pd.DataFrame({"y": [1]}), pf)

        assert isinstance(result.children[1], dag.AgGrid)

    def test_small_screen_routes_charts_through_mobile_config(self):
        from pages.portfolio.portfolio import (
            get_forecast_survival_statistics_section,
            get_forecast_wealth_statistics_section,
        )

        pf = _pf_with_mc_stats()
        screen = {"in_width": 375}
        survival = get_forecast_survival_statistics_section(
            pd.DataFrame({"x": [1]}), pd.DataFrame(), pf, compact=True, screen=screen
        )
        wealth = get_forecast_wealth_statistics_section(pf, compact=True, screen=screen)

        assert _section_graph(survival).config["displayModeBar"] is False
        assert _section_graph(wealth).config["displayModeBar"] is False

    def test_inner_builds_compact_tables_on_small_screen(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        patched_pf_inner.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
        wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
        patched_pf_inner.dcf.monte_carlo_wealth = MagicMock(
            side_effect=lambda discounting="fv", include_negative_values=True: (
                wealth_fv if discounting == "fv" else wealth_fv / 2
            )
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
        survival_grid = _section_grid(result[3])
        wealth_grid = _section_grid(result[4])
        assert len(survival_grid.rowData) == 11  # 7 percentiles + Min/Max/Mean/Std
        assert len(wealth_grid.rowData) == 12  # + Discount rate


class TestGetPfFigureAnnualReturn:
    def test_annual_return_renders_bar_chart(self):
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, df_backtest, df_forecast, df_data = get_pf_figure(
            pf,
            plot_type="annual_return",
            inflation_on=False,
            rolling_window=2,
            n_monte_carlo=0,
            years_monte_carlo=0,
            distribution_monte_carlo="norm",
            show_backtest="no",
            log_scale=False,
            cf_strategy="indexation",
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
            pf,
            plot_type="annual_return",
            inflation_on=False,
            rolling_window=2,
            n_monte_carlo=0,
            years_monte_carlo=0,
            distribution_monte_carlo="norm",
            show_backtest="no",
            log_scale=False,
            cf_strategy="indexation",
        )
        pf.annual_return_ts.assert_called_once_with(return_type="cagr")
        assert "CAGR" in fig.layout.title.subtitle.text


class TestGetPfFigureWealthAnnotations:
    def test_wealth_plot_annotates_each_trace_with_balance_points(self):
        from common.chart_helpers import format_points
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        fig, *_ = get_pf_figure(
            pf,
            plot_type="wealth",
            inflation_on=False,
            rolling_window=2,
            n_monte_carlo=0,
            years_monte_carlo=0,
            distribution_monte_carlo="norm",
            show_backtest="no",
            log_scale=False,
            cf_strategy="indexation",
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
            pf,
            plot_type="cumulative_return",
            inflation_on=False,
            rolling_window=2,
            n_monte_carlo=0,
            years_monte_carlo=0,
            distribution_monte_carlo="norm",
            show_backtest="no",
            log_scale=False,
            cf_strategy="indexation",
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
        assert all(d["valueFormatter"]["function"] == "formatPercentGuarded(params.value)" for d in grid.columnDefs)


def _irr_pf(series, hist=0.045):
    pf = _pf_with_mc_stats()
    pf.dcf.monte_carlo_irr.return_value = pd.Series(series, dtype="float64")
    pf.dcf.irr.return_value = hist
    return pf


class TestCashflowIrrSection:
    """Issue #19: third MC section — CashFlow IRR (percentile table + histogram)."""

    @staticmethod
    def _build(pf, **kwargs):
        from pages.portfolio.portfolio import get_forecast_cashflow_irr_statistics_section

        return get_forecast_cashflow_irr_statistics_section(pf, **kwargs)

    # The Table tab wraps grid + effective-sample note in one Div.
    @staticmethod
    def _grid(section):
        return _section_tabs(section).children[0].children.children[0]

    @staticmethod
    def _note(section):
        return _section_tabs(section).children[0].children.children[1]

    def test_section_has_table_and_distribution_tabs(self):
        section = self._build(_irr_pf([0.04, 0.05, 0.06]))

        tabs = _section_tabs(section)
        assert type(tabs).__name__ == "Tabs"
        assert [tab.label for tab in tabs.children] == ["Table", "Distribution"]

    def test_table_grid_id_matches_the_export_wiring(self):
        section = self._build(_irr_pf([0.04, 0.05, 0.06]))

        assert self._grid(section).id == "pf-cashflow-irr-statistics-grid"

    def test_statistics_computed_on_non_nan_subset(self):
        section = self._build(_irr_pf([0.04, float("nan"), 0.06]))

        right_pane = {row["3"]: row["4"] for row in self._grid(section).rowData}
        assert right_pane["Min"] == pytest.approx(0.04)
        assert right_pane["Max"] == pytest.approx(0.06)
        assert right_pane["Mean"] == pytest.approx(0.05)

    def test_effective_sample_note_shows_n_of_total(self):
        section = self._build(_irr_pf([0.04, float("nan"), 0.06]))

        assert "2 of 3" in self._note(section).children

    def test_historical_irr_row_present(self):
        section = self._build(_irr_pf([0.04, 0.05, 0.06], hist=0.045))

        right_pane = {row["3"]: row["4"] for row in self._grid(section).rowData}
        assert right_pane["Historical IRR"] == pytest.approx(0.045)

    def test_nan_historical_irr_rendered_as_none(self):
        # NaN is not valid JSON; the guarded formatter renders None as a dash.
        section = self._build(_irr_pf([0.04, 0.06], hist=float("nan")))

        right_pane = {row["3"]: row["4"] for row in self._grid(section).rowData}
        assert right_pane["Historical IRR"] is None

    def test_all_nan_renders_graceful_note(self):
        section = self._build(_irr_pf([float("nan")] * 3))

        assert "undefined" in str(section.children[1].children)
        assert "Tabs" not in [type(c).__name__ for c in section.children]

    def test_values_use_guarded_percent_formatter(self):
        section = self._build(_irr_pf([0.04, 0.05, 0.06]))

        value_defs = [d for d in self._grid(section).columnDefs if "valueFormatter" in d]
        assert value_defs, "no value columns found"
        assert all(d["valueFormatter"]["function"] == "formatPercentGuarded(params.value)" for d in value_defs)

    def test_histogram_plots_non_nan_values_with_percent_ticks(self):
        section = self._build(_irr_pf([0.04, float("nan"), 0.06]))

        figure = _section_graph(section).figure
        assert figure.data[0].histnorm == "probability"
        assert list(figure.data[0].x) == [0.04, 0.06]
        assert figure.layout.xaxis.tickformat == ".1%"

    def test_compact_stacks_pairs_in_single_column(self):
        section = self._build(_irr_pf([0.04, 0.05, 0.06]), compact=True)

        grid = self._grid(section)
        assert len(grid.rowData) == 12  # 7 percentiles + Min/Max/Mean/Std + Historical IRR
        assert all(set(row) == {"1", "2"} for row in grid.rowData)

    def test_inner_returns_irr_section_before_chart_data(self, patched_pf_inner):
        from pages.portfolio.portfolio import _update_graf_portfolio_inner

        patched_pf_inner.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
        wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
        patched_pf_inner.dcf.monte_carlo_wealth = MagicMock(
            side_effect=lambda discounting="fv", include_negative_values=True: (
                wealth_fv if discounting == "fv" else wealth_fv / 2
            )
        )
        patched_pf_inner.dcf.monte_carlo_irr.return_value = pd.Series([0.04, 0.05, 0.06])
        patched_pf_inner.dcf.irr.return_value = 0.045
        args = _default_args()
        args["n_monte_carlo"] = 2
        with patch(
            f"{PF_MODULE}.get_pf_figure",
            return_value=(go.Figure(), pd.DataFrame(), pd.DataFrame({0: [1.0]}), pd.DataFrame()),
        ):
            result = _update_graf_portfolio_inner(**args)

        assert len(result) == 7
        assert self._grid(result[5]).id == "pf-cashflow-irr-statistics-grid"


class TestUpdateGrafPortfolioOuter:
    # Outputs: fig, config, stats, survival, wealth, cashflow IRR, chart data,
    # toast is_open, toast children — toast sits at positions 7/8.
    def test_exception_opens_toast_with_message(self):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,
            patch(f"{PF_MODULE}._update_graf_portfolio_inner", side_effect=ValueError("boom")),
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(),
                n_clicks=1,
            )

        toast_is_open = result[7]
        toast_children = result[8]
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
                **_default_args(),
                n_clicks=1,
            )

        assert len(result) == 9

    def test_success_closes_toast(self, patched_pf_inner):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            result = update_graf_portfolio(
                **_default_args(),
                n_clicks=1,
            )

        assert result[7] is False
        assert len(result) == 9

    def test_log_scale_toggle_no_update_toast(self):
        import dash
        from pages.portfolio.portfolio import update_graf_portfolio

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-logarithmic-scale-switch"
            args = _default_args()
            args["log_on"] = True
            result = update_graf_portfolio(
                **args,
                n_clicks=1,
            )

        assert result[7] is dash.no_update
        assert result[8] is dash.no_update


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
            pf,
            has_cashflow=True,
            n_monte_carlo=2,
            show_backtest_bool=False,
            distribution_mc="norm",
            years_mc=5,
        )

        dead = df_forecast[0]
        assert dead.loc[dates[2]] == 0  # death point kept at exactly zero
        assert dead.loc[dates[3] :].isna().all()  # line breaks after death

    def test_surviving_scenario_keeps_all_values(self):
        from pages.portfolio.portfolio import _get_wealth_data

        pf, _ = self._portfolio_with_mc_forecast()
        _, _, df_forecast, _ = _get_wealth_data(
            pf,
            has_cashflow=True,
            n_monte_carlo=2,
            show_backtest_bool=False,
            distribution_mc="norm",
            years_mc=5,
        )

        alive = df_forecast[1]
        assert alive.notna().all()
        assert (alive > 0).all()

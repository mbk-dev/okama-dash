from unittest.mock import patch

import dash_ag_grid as dag
import plotly.graph_objects as go
import pytest

from tests.mocks.okama_mock import make_mock_asset_list

pytestmark = pytest.mark.component

COMPARE_MODULE = "pages.compare.compare"


@pytest.fixture
def mock_al():
    al = make_mock_asset_list(["AAPL.US", "MSFT.US"])
    with patch(f"{COMPARE_MODULE}.ok.AssetList", return_value=al):
        yield al


class TestUpdateGrafCompareInner:
    def test_wealth_returns_figure_and_table(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, config, table, json_data = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="wealth",
            inflation_on=False,
            rolling_window=2,
        )
        assert isinstance(fig, go.Figure)
        assert isinstance(config, dict)
        assert isinstance(table, dag.AgGrid)
        assert len(table.rowData) > 0
        assert json_data is not None

    def test_cagr_plot_type(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, _, _, _ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="cagr",
            inflation_on=False,
            rolling_window=2,
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.yaxis.title.text == "CAGR"

    def test_correlation_plot_type(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, _, _, _ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="correlation",
            inflation_on=False,
            rolling_window=2,
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.showlegend is False

    def test_cumulative_return_plot_type(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, _, _, _ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="cumulative_return",
            inflation_on=False,
            rolling_window=2,
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.yaxis.title.text == "Cumulative Return"

    def test_annual_return_plot_type_renders_bar_chart(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, _, _, _ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="annual_return",
            inflation_on=False,
            rolling_window=2,
        )
        assert isinstance(fig, go.Figure)
        assert fig.layout.yaxis.title.text == "Annual Return, %"
        assert len(fig.data) > 0
        assert all(trace.type == "bar" for trace in fig.data)

    def test_annual_return_bars_anchored_at_year_start(self, mock_al):
        # Regression: bars must sit at Jan 1 so each aligns under its own year tick
        # (dtick="M12" + instant ticks anchor on Jan 1). Year-end placement read every
        # bar one year too high — the latest YTD bar showed as a future year.
        import pandas as pd

        from pages.compare.compare import _update_graf_compare_inner

        fig, *_ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="annual_return",
            inflation_on=False,
            rolling_window=2,
        )
        for trace in fig.data:
            x = pd.DatetimeIndex(trace.x)
            assert list(x.month) == [1] * len(x)
            assert list(x.day) == [1] * len(x)

    def test_annual_return_chart_annotates_cagr_return_type(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        fig, *_ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="annual_return",
            inflation_on=False,
            rolling_window=2,
        )
        assert "CAGR" in fig.layout.title.subtitle.text

    def test_statistics_table_has_data(self, mock_al):
        from pages.compare.compare import _update_graf_compare_inner

        _, _, table, _ = _update_graf_compare_inner(
            screen=None,
            log_on=False,
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="wealth",
            inflation_on=False,
            rolling_window=2,
        )
        assert len(table.rowData) > 0


class TestWealthAnnotationsInPoints:
    def test_wealth_annotations_show_balance_points(self):
        from common.chart_helpers import format_points
        from pages.compare.compare import get_al_figure

        al = make_mock_asset_list(["AAPL.US", "MSFT.US"])
        fig, _ = get_al_figure(al, "wealth", inflation_on=False, rolling_window=2, log_scale=False)
        texts = [a.text for a in fig.layout.annotations if a.text]
        for value in al.wealth_indexes.iloc[-1]:
            assert format_points(value) in texts
        assert not any(t.endswith("%") for t in texts)

    def test_cumulative_return_annotations_stay_percent(self):
        from pages.compare.compare import get_al_figure

        al = make_mock_asset_list(["AAPL.US", "MSFT.US"])
        fig, _ = get_al_figure(al, "cumulative_return", inflation_on=False, rolling_window=2, log_scale=False)
        expected = list((al.get_cumulative_return(real=False).iloc[-1] * 100).map("{:,.2f}%".format))
        texts = [a.text for a in fig.layout.annotations if a.text]
        for percent_text in expected:
            assert percent_text in texts


class TestStatisticsGridDotNotation:
    def test_al_statistics_grid_suppresses_field_dot_notation(self):
        # Ticker column names contain dots (AAPL.US); without suppressFieldDotNotation
        # AG Grid treats them as nested paths and renders the metric columns empty.
        from pages.compare.compare import get_al_statistics_table

        grid = get_al_statistics_table(make_mock_asset_list(["AAPL.US", "MSFT.US"]))
        assert grid.dashGridOptions.get("suppressFieldDotNotation") is True

    def test_al_statistics_columns_use_guarded_percent_function(self):
        # Inline typeof-guards are not supported by the dash-ag-grid function-string
        # parser; columns must call the registered assets/dashAgGridFunctions.js helper.
        from pages.compare.compare import get_al_statistics_table

        grid = get_al_statistics_table(make_mock_asset_list(["AAPL.US", "MSFT.US"]))
        assert all(d["valueFormatter"]["function"] == "formatPercentGuarded(params.value)" for d in grid.columnDefs)


class TestUpdateGrafCompareOuter:
    def test_empty_symbols_raises_prevent_update(self):
        from pages.compare.compare import update_graf_compare
        import dash.exceptions

        with patch(f"{COMPARE_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "al-submit-button"
            with pytest.raises(dash.exceptions.PreventUpdate):
                update_graf_compare(
                    screen=None,
                    n_clicks=1,
                    log_on=False,
                    selected_symbols=[],
                    ccy="USD",
                    fd_value="2020-01",
                    ld_value="2024-12",
                    plot_type="wealth",
                    inflation_on=False,
                    rolling_window=2,
                    pf_def=None,
                )

    def test_exception_returns_empty_figure(self):
        from pages.compare.compare import update_graf_compare

        with (
            patch(f"{COMPARE_MODULE}.dash.ctx") as mock_ctx,
            patch(f"{COMPARE_MODULE}.ok.AssetList", side_effect=ValueError("bad data")),
        ):
            mock_ctx.triggered_id = "al-submit-button"
            fig, config, alert, json_data = update_graf_compare(
                screen=None,
                n_clicks=1,
                log_on=False,
                selected_symbols=["AAPL.US"],
                ccy="USD",
                fd_value="2020-01",
                ld_value="2024-12",
                plot_type="wealth",
                inflation_on=False,
                rolling_window=2,
                pf_def=None,
            )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert json_data is None

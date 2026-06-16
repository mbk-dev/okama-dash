from unittest.mock import patch

import plotly.graph_objects as go
import pytest

from tests.mocks.okama_mock import make_mock_asset_list

pytestmark = pytest.mark.component

BENCHMARK_MODULE = "pages.benchmark.benchmark"


@pytest.fixture
def mock_al():
    al = make_mock_asset_list(["SP500TR.INDX", "AAPL.US", "MSFT.US"])
    with patch(f"{BENCHMARK_MODULE}.ok.AssetList", return_value=al):
        yield al


class TestUpdateGrafBenchmark:
    @pytest.mark.parametrize("plot_type", ["td", "annualized_td", "te", "correlation", "beta"])
    def test_rolling_plot_types_return_figure(self, mock_al, plot_type):
        from pages.benchmark.benchmark import update_graf_benchmark

        fig, config, json_data = update_graf_benchmark(
            screen=None,
            n_clicks=1,
            benchmark="SP500TR.INDX",
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type=plot_type,
            expanding_rolling="rolling",
            rolling_window=2,
            pf_def=None,
        )
        assert isinstance(fig, go.Figure)
        assert isinstance(config, dict)
        assert json_data is not None

    def test_annual_td_bar_returns_bar_chart(self, mock_al):
        from pages.benchmark.benchmark import update_graf_benchmark

        fig, _, _ = update_graf_benchmark(
            screen=None,
            n_clicks=1,
            benchmark="SP500TR.INDX",
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="annual_td_bar",
            expanding_rolling="rolling",
            rolling_window=2,
            pf_def=None,
        )
        assert isinstance(fig, go.Figure)
        assert any(isinstance(t, go.Bar) for t in fig.data)

    def test_annual_td_bar_bars_anchored_at_year_start(self, mock_al):
        # Regression: bars must sit at Jan 1 so each aligns under its own year tick
        # (dtick="M12" + instant ticks anchor on Jan 1). Year-end placement read every
        # bar one year too high — the latest YTD bar showed as a future year.
        import pandas as pd

        from pages.benchmark.benchmark import get_benchmark_figure

        fig, _ = get_benchmark_figure(mock_al, "annual_td_bar", "rolling", 2)
        bars = [t for t in fig.data if isinstance(t, go.Bar)]
        assert bars
        for trace in bars:
            x = pd.DatetimeIndex(trace.x)
            assert list(x.month) == [1] * len(x)
            assert list(x.day) == [1] * len(x)

    def test_empty_symbols_raises_prevent_update(self):
        from pages.benchmark.benchmark import update_graf_benchmark
        import dash.exceptions

        with pytest.raises(dash.exceptions.PreventUpdate):
            update_graf_benchmark(
                screen=None,
                n_clicks=1,
                benchmark="SP500TR.INDX",
                selected_symbols=[],
                ccy="USD",
                fd_value="2020-01",
                ld_value="2024-12",
                plot_type="td",
                expanding_rolling="rolling",
                rolling_window=2,
                pf_def=None,
            )

    def test_no_benchmark_raises_prevent_update(self):
        from pages.benchmark.benchmark import update_graf_benchmark
        import dash.exceptions

        with pytest.raises(dash.exceptions.PreventUpdate):
            update_graf_benchmark(
                screen=None,
                n_clicks=1,
                benchmark=None,
                selected_symbols=["AAPL.US"],
                ccy="USD",
                fd_value="2020-01",
                ld_value="2024-12",
                plot_type="td",
                expanding_rolling="rolling",
                rolling_window=2,
                pf_def=None,
            )

    def test_exception_returns_error_figure(self):
        from pages.benchmark.benchmark import update_graf_benchmark

        with patch(f"{BENCHMARK_MODULE}.ok.AssetList", side_effect=ValueError("bad")):
            fig, config, json_data = update_graf_benchmark(
                screen=None,
                n_clicks=1,
                benchmark="SP500TR.INDX",
                selected_symbols=["AAPL.US"],
                ccy="USD",
                fd_value="2020-01",
                ld_value="2024-12",
                plot_type="td",
                expanding_rolling="rolling",
                rolling_window=2,
                pf_def=None,
            )
        assert isinstance(fig, go.Figure)
        assert json_data is None

    def test_expanding_window_passes_none(self, mock_al):
        from pages.benchmark.benchmark import update_graf_benchmark

        update_graf_benchmark(
            screen=None,
            n_clicks=1,
            benchmark="SP500TR.INDX",
            selected_symbols=["AAPL.US", "MSFT.US"],
            ccy="USD",
            fd_value="2020-01",
            ld_value="2024-12",
            plot_type="td",
            expanding_rolling="expanding",
            rolling_window=2,
            pf_def=None,
        )
        mock_al.tracking_difference.assert_called_with(rolling_window=None)

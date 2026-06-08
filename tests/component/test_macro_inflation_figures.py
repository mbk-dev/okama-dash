"""Figure-builder tests for the Inflation page (pure functions over mock objects)."""

from unittest.mock import patch

import pandas as pd
import pytest

from tests.mocks.okama_mock import PicklableInflation, PicklableRate

pytestmark = pytest.mark.component


@pytest.fixture
def objects():
    return [PicklableInflation("RUB.INFL"), PicklableInflation("USD.INFL")]


class TestInflationFigure:
    def test_annual_plot_is_grouped_bars_with_country_names(self, objects):
        from pages.macro.inflation import get_inflation_figure

        fig, _ = get_inflation_figure(objects, "annual")
        assert all(trace.type == "bar" for trace in fig.data)
        assert {trace.name for trace in fig.data} == {"Russia", "USA"}
        assert fig.layout.barmode == "group"

    def test_rolling_plot_is_lines_in_percent(self, objects):
        from pages.macro.inflation import get_inflation_figure

        fig, _ = get_inflation_figure(objects, "rolling12m")
        assert all(trace.type == "scatter" for trace in fig.data)
        # fractions are converted to percent for the chart
        rolling_max = max(obj.rolling_inflation.max() for obj in objects)
        assert max(max(t.y) for t in fig.data) > rolling_max  # x100 applied

    def test_cumulative_and_monthly_plots_build(self, objects):
        from pages.macro.inflation import get_inflation_figure

        for plot_type in ("cumulative", "monthly"):
            fig, _ = get_inflation_figure(objects, plot_type)
            assert len(fig.data) == 2

    def test_y_axis_title_mentions_percent(self, objects):
        from pages.macro.inflation import get_inflation_figure

        fig, _ = get_inflation_figure(objects, "annual")
        assert "%" in fig.layout.yaxis.title.text

    def test_builder_returns_dataframe(self, objects):
        from pages.macro.inflation import get_inflation_figure

        fig, df = get_inflation_figure(objects, "annual")
        assert list(df.columns) == ["Russia", "USA"]

    def test_monthly_plot_is_bars_with_highlighted_last(self, objects):
        from pages.macro.inflation import get_inflation_figure

        fig, df = get_inflation_figure(objects, "monthly")
        assert all(t.type == "bar" for t in fig.data)
        colors = fig.data[0].marker.color
        assert isinstance(colors, (list, tuple))
        assert colors[-1] != colors[0]


class TestKeyRateOverlay:
    def test_overlay_adds_step_traces_for_mapped_rates(self, objects):
        from pages.macro import inflation as infl_page

        fig, _ = infl_page.get_inflation_figure(objects, "rolling12m")
        base_traces = len(fig.data)
        with patch.object(
            infl_page.macro_objects, "get_rate_object", side_effect=lambda s, fd, ld: PicklableRate(s)
        ) as get_rate:
            infl_page.add_key_rate_overlay(fig, ["RUB.INFL", "USD.INFL"], "2000-01", "2026-05")
        assert len(fig.data) == base_traces + 2
        overlay = fig.data[-1]
        assert overlay.line.shape == "hv"  # rates change stepwise
        assert overlay.line.dash == "dot"
        called_symbols = {call.args[0] for call in get_rate.call_args_list}
        assert called_symbols == {"RUS_CBR.RATE", "US_EFFR.RATE"}

    def test_overlay_trace_names_are_rate_labels(self, objects):
        from pages.macro import inflation as infl_page

        fig, _ = infl_page.get_inflation_figure(objects, "annual")
        with patch.object(infl_page.macro_objects, "get_rate_object", side_effect=lambda s, fd, ld: PicklableRate(s)):
            infl_page.add_key_rate_overlay(fig, ["RUB.INFL"], None, None)
        assert fig.data[-1].name == "Bank of Russia key rate"


class TestPurchasingPowerCards:
    def test_one_card_per_object_with_currency_and_value(self, objects):
        from pages.macro.inflation import get_purchasing_power_cards

        row = get_purchasing_power_cards(objects)
        assert len(row.children) == 2
        rendered = str(row.children[0])
        assert "1000 RUB" in rendered
        assert "785" in rendered  # PicklableInflation.purchasing_power_1000

    def test_nan_purchasing_power_falls_back_to_last_valid(self):
        from pages.macro.inflation import get_purchasing_power_cards

        class _NanPP:
            symbol = "EUR.INFL"
            purchasing_power_1000 = float("nan")
            first_date = pd.Timestamp("2000-01-01")
            last_date = pd.Timestamp("2026-04-01")
            cumulative_inflation = pd.Series(
                [0.5, 0.9147], index=pd.period_range("2026-03", "2026-04", freq="M")
            )

        row = get_purchasing_power_cards([_NanPP()])
        rendered = str(row.children[0])
        assert "nan" not in rendered.lower()
        assert "522" in rendered

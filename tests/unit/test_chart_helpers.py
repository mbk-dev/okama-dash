import pandas as pd
import plotly.graph_objects as go
import pytest

from common.chart_helpers import add_return_type_subtitle, annual_bar_figure

pytestmark = pytest.mark.unit


class TestAnnualBarFigure:
    def test_bars_anchored_at_year_start_to_align_with_year_ticks(self):
        # Year ticks are drawn with dtick="M12" + ticklabelmode="instant", which
        # plotly anchors on Jan 1. Bars must therefore sit at the year START so each
        # lands under its own year tick; year END (Dec 31) put every bar one day
        # before the NEXT year's tick, reading one year too high (the future-year bug).
        idx = pd.period_range("2020", "2024", freq="Y")
        df = pd.DataFrame({"A": range(5), "B": range(5)}, index=idx)
        fig = annual_bar_figure(df, title="t", height=400)
        for trace in fig.data:
            x = pd.DatetimeIndex(trace.x)
            assert list(x.month) == [1] * len(x)
            assert list(x.day) == [1] * len(x)
            assert list(x.year) == list(idx.year)
        assert fig.layout.xaxis.dtick == "M12"
        assert fig.layout.xaxis.tickformat == "%Y"
        assert fig.layout.xaxis.ticklabelmode == "instant"

    def test_barmode_is_configurable(self):
        idx = pd.period_range("2020", "2024", freq="Y")
        df = pd.DataFrame({"A": range(5)}, index=idx)
        fig = annual_bar_figure(df, barmode="relative")
        assert fig.layout.barmode == "relative"


class TestFormatPoints:
    def test_rounds_to_integer_and_separates_thousands_with_space(self):
        from common.chart_helpers import format_points

        assert format_points(13456.78) == "13 457"

    def test_value_below_thousand_has_no_separator(self):
        from common.chart_helpers import format_points

        assert format_points(999.4) == "999"

    def test_millions_get_two_separators(self):
        from common.chart_helpers import format_points

        assert format_points(1234567.89) == "1 234 568"


class TestAddReturnTypeSubtitle:
    def test_adds_cagr_note(self):
        fig = go.Figure()
        add_return_type_subtitle(fig, "CAGR")
        assert "CAGR" in fig.layout.title.subtitle.text

    def test_defaults_to_cagr(self):
        fig = go.Figure()
        add_return_type_subtitle(fig)
        assert "CAGR" in fig.layout.title.subtitle.text

    def test_title_and_subtitle_are_left_aligned(self):
        fig = go.Figure()
        add_return_type_subtitle(fig)
        assert fig.layout.title.x == 0
        assert fig.layout.title.xanchor == "left"

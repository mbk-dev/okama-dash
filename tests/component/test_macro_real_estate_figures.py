"""Figure-builder tests for the Real Estate page (pure functions over mocks)."""

import pandas as pd
import pytest

from tests.mocks.okama_mock import PicklableAsset, PicklableAssetList

pytestmark = pytest.mark.component


class TestTrimFuture:
    def test_future_points_are_dropped(self):
        from pages.macro.real_estate import trim_future

        now = pd.Timestamp.today().to_period("M")
        idx = pd.period_range(now - 3, now + 9, freq="M")  # 9 months of "forecast"
        series = pd.Series(range(len(idx)), index=idx, name="MOW_PR.RE")
        trimmed = trim_future(series)
        assert trimmed.index.max() == now
        assert len(trimmed) == 4

    def test_past_only_series_unchanged(self):
        from pages.macro.real_estate import trim_future

        idx = pd.period_range("2020-01", "2020-12", freq="M")
        series = pd.Series(range(12), index=idx)
        pd.testing.assert_series_equal(trim_future(series), series)


class TestPriceFigure:
    def test_rub_prices_with_labels(self):
        from pages.macro.real_estate import get_re_price_figure

        prices = {
            "MOW_PR.RE": PicklableAsset("MOW_PR.RE").close_monthly,
            "MOW_SEC.RE": PicklableAsset("MOW_SEC.RE").close_monthly,
        }
        fig = get_re_price_figure(prices, ccy="RUB")
        assert {t.name for t in fig.data} == {"Moscow primary market", "Moscow secondary market"}
        assert "RUB" in fig.layout.yaxis.title.text
        assert max(fig.data[0].y) > 1000  # absolute prices, not returns

    def test_usd_axis_title(self):
        from pages.macro.real_estate import get_re_price_figure

        prices = {"MOW_PR.RE": PicklableAsset("MOW_PR.RE").close_monthly / 80.0}
        fig = get_re_price_figure(prices, ccy="USD")
        assert "USD" in fig.layout.yaxis.title.text


class TestWealthFigure:
    def test_wealth_lines_include_inflation(self):
        from pages.macro.real_estate import get_re_wealth_figure

        al = PicklableAssetList(["MOW_PR.RE", "MOW_SEC.RE"], ccy="RUB", inflation=True)
        fig = get_re_wealth_figure(al)
        names = {t.name for t in fig.data}
        assert "Moscow primary market" in names
        assert "RUB.INFL" in names  # inflation reference line keeps its symbol name
        assert len(fig.data) == 3

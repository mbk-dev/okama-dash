"""Tests for /macro/rates: step-line figure, main callback, auto-render, prefill."""

from unittest.mock import patch

import dash
import pytest

from tests.mocks.okama_mock import PicklableRate

pytestmark = pytest.mark.component


@pytest.fixture
def rates_page():
    from pages.macro import rates

    return rates


@pytest.fixture
def patched_rates(rates_page):
    from tests.mocks.okama_mock import PicklableInflation

    with (
        patch.object(rates_page.macro_objects, "get_rate_object", side_effect=lambda s, fd, ld: PicklableRate(s)),
        patch.object(
            rates_page.macro_objects, "get_inflation_object", side_effect=lambda s, fd, ld: PicklableInflation(s)
        ),
    ):
        yield


class TestRatesFigure:
    def test_step_lines_with_series_labels(self, rates_page):
        objects = [PicklableRate("RUS_CBR.RATE"), PicklableRate("US_EFFR.RATE")]
        fig, _ = rates_page.get_rates_figure(objects)
        assert len(fig.data) == 2
        assert all(trace.line.shape == "hv" for trace in fig.data)
        assert {trace.name for trace in fig.data} == {"Bank of Russia key rate", "US Fed effective funds rate"}

    def test_values_scaled_to_percent(self, rates_page):
        objects = [PicklableRate("RUS_CBR.RATE")]
        fig, _ = rates_page.get_rates_figure(objects)
        assert max(fig.data[0].y) > 1  # fractions ×100


class TestRealRateFigure:
    def test_real_rate_uses_rate_minus_inflation(self, rates_page):
        from tests.mocks.okama_mock import PicklableInflation

        rate = PicklableRate("RUS_CBR.RATE")
        infl = PicklableInflation("RUB.INFL")
        fig, df = rates_page.get_real_rates_figure({"RUS_CBR.RATE": (rate, infl)})
        assert fig.data[0].name == "Bank of Russia key rate"
        assert "Real" in fig.layout.title.text

    def test_empty_pairs_raises_clear_error(self, rates_page):
        # No selected rate has an inflation mapping -> a clear message, not an
        # opaque RangeIndex.to_timestamp crash (caught by the page as an annotation).
        with pytest.raises(ValueError, match="inflation"):
            rates_page.get_real_rates_figure({})


class TestMainCallback:
    def test_history_returns_figure_and_store(self, rates_page, patched_rates):
        fig, config, store = rates_page.update_rates_page(None, ["RUS_CBR.RATE", "US_EFFR.RATE"], "history")
        assert len(fig.data) == 2
        assert all(t.line.shape == "hv" for t in fig.data)
        assert isinstance(store, str) and "columns" in store

    def test_real_rates_subtracts_inflation(self, rates_page, patched_rates):
        fig_nom, *_ = rates_page.update_rates_page(None, ["RUS_CBR.RATE"], "history")
        fig_real, *_ = rates_page.update_rates_page(None, ["RUS_CBR.RATE"], "real")
        assert max(fig_real.data[0].y) < max(fig_nom.data[0].y)

    def test_snapshot_mode_renders_bar(self, rates_page, patched_rates):
        with patch.object(rates_page, "get_or_create", side_effect=lambda **kw: (kw["constructor_fn"](), "k")):
            fig, config, store = rates_page.update_rates_page(None, ["RUS_CBR.RATE"], "snapshot")
        assert fig.data[0].type == "bar"
        assert fig.data[0].orientation == "h"

    def test_empty_selection_prevents_update(self, rates_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            rates_page.update_rates_page(None, [], "history")

    def test_error_renders_annotation(self, rates_page):
        with patch.object(rates_page.macro_objects, "get_rate_object", side_effect=ValueError("api down")):
            fig, config, store = rates_page.update_rates_page(None, ["RUS_CBR.RATE"], "history")
        assert fig.layout.annotations[0].text == "api down"
        assert store is None

    def test_every_control_is_an_input(self, rates_page):
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "rates-chart.figure" in str(s["output"]))
        inputs = str(spec["inputs"])
        for control in ("rates-series", "rates-plot-type"):
            assert control in inputs
        assert "first-date" not in inputs and "last-date" not in inputs
        assert "submit" not in inputs
        assert "rates-group" not in inputs
        assert not spec["state"]


class TestLayoutAndLink:
    def test_url_prefill_and_defaults(self, rates_page, mock_okama_symbols, null_cache):
        from pages.macro.macro_data import RATES_DEFAULTS

        page = rates_page.layout(tickers="RUS_CBR.RATE,FAKE.RATE")
        select = _find_by_id(page, "rates-series")
        assert select.value == ["RUS_CBR.RATE"]
        page_default = rates_page.layout()
        assert _find_by_id(page_default, "rates-series").value == RATES_DEFAULTS

    def test_layout_prefills_plot_type(self, rates_page, mock_okama_symbols, null_cache):
        assert _find_by_id(rates_page.layout(), "rates-plot-type").value == "history"
        assert _find_by_id(rates_page.layout(plot="real"), "rates-plot-type").value == "real"

    def test_link_callback(self, rates_page):
        link = rates_page.update_rates_link(1, "http://x/macro/rates", ["RUS_CBR.RATE"], "key", "history")
        assert link == "http://x/macro/rates?tickers=RUS_CBR.RATE"

    def test_link_carries_non_default_group_and_plot(self, rates_page):
        link = rates_page.update_rates_link(1, "http://x/macro/rates", ["RUONIA.RATE"], "mm", "real")
        assert "group=mm" in link and "plot=real" in link

    def test_empty_selection_disables_copy_link(self, rates_page):
        assert rates_page.disable_copy_link_rates([]) is True
        assert rates_page.disable_copy_link_rates(["RUS_CBR.RATE"]) is False


class TestGroupSelector:
    def test_switch_group_swaps_options_and_defaults(self, rates_page):
        from pages.macro.macro_data import MONEY_MARKET_SERIES

        options, value = rates_page.switch_rates_group("mm")
        assert value == ["RUONIA.RATE"]
        assert {o["value"] for o in options} == set(MONEY_MARKET_SERIES)

    def test_unknown_group_falls_back_to_key(self, rates_page):
        from pages.macro.macro_data import KEY_RATES_SERIES, RATES_DEFAULTS

        options, value = rates_page.switch_rates_group("nope")
        assert value == RATES_DEFAULTS
        assert {o["value"] for o in options} == set(KEY_RATES_SERIES)

    def test_group_is_not_a_main_callback_input(self, rates_page):
        # The group switch updates the series multiselect, whose value change
        # then triggers the main callback — wiring the group directly would
        # double-fire the recalc with a stale series list.
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "rates-chart.figure" in str(s["output"]))
        assert "rates-group" not in str(spec["inputs"])

    def test_layout_prefills_group_and_group_scoped_tickers(self, rates_page, mock_okama_symbols, null_cache):
        page = rates_page.layout(group="mm", tickers="RUONIA.RATE,FAKE.RATE")
        assert _find_by_id(page, "rates-group").value == "mm"
        assert _find_by_id(page, "rates-series").value == ["RUONIA.RATE"]
        # tickers from another group are dropped -> group defaults
        page2 = rates_page.layout(group="mm", tickers="RUS_CBR.RATE")
        assert _find_by_id(page2, "rates-series").value == ["RUONIA.RATE"]

    def test_main_callback_renders_money_market_series(self, rates_page, patched_rates):
        fig, *_ = rates_page.update_rates_page(None, ["RUONIA.RATE"], "history")
        assert fig.data[0].name == "RUONIA"


def _find_by_id(component, component_id):
    stack = [component]
    while stack:
        node = stack.pop()
        if getattr(node, "id", None) == component_id:
            return node
        children = getattr(node, "children", None)
        children = children if isinstance(children, list) else [children] if children is not None else []
        stack.extend(children)
    raise AssertionError(f"id {component_id} not found")

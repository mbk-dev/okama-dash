"""Tests for /macro/rates: step-line figure, main callback, auto-render, prefill."""

from unittest.mock import patch

import dash
import plotly.graph_objects as go
import pytest

from tests.mocks.okama_mock import PicklableRate

pytestmark = pytest.mark.component


@pytest.fixture
def rates_page():
    from pages.macro import rates

    return rates


@pytest.fixture
def patched_rates(rates_page):
    with patch.object(
        rates_page.macro_objects, "get_rate_object", side_effect=lambda s, fd, ld: PicklableRate(s)
    ):
        yield


class TestRatesFigure:
    def test_step_lines_with_series_labels(self, rates_page):
        objects = [PicklableRate("RUS_CBR.RATE"), PicklableRate("US_EFFR.RATE")]
        fig = rates_page.get_rates_figure(objects)
        assert len(fig.data) == 2
        assert all(trace.line.shape == "hv" for trace in fig.data)
        assert {trace.name for trace in fig.data} == {"Bank of Russia key rate", "US Fed effective funds rate"}

    def test_values_scaled_to_percent(self, rates_page):
        objects = [PicklableRate("RUS_CBR.RATE")]
        fig = rates_page.get_rates_figure(objects)
        assert max(fig.data[0].y) > 1  # fractions ×100


class TestMainCallback:
    def test_returns_figure_and_grid(self, rates_page, patched_rates):
        fig, config, grid = rates_page.update_rates_page(
            None, ["RUS_CBR.RATE", "US_EFFR.RATE"], "2000-01", "2026-05"
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert grid.id == "rates-describe-table-grid"

    def test_empty_selection_prevents_update(self, rates_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            rates_page.update_rates_page(None, [], None, None)

    def test_error_renders_annotation(self, rates_page):
        with patch.object(rates_page.macro_objects, "get_rate_object", side_effect=ValueError("api down")):
            fig, config, grid = rates_page.update_rates_page(None, ["RUS_CBR.RATE"], None, None)
        assert fig.layout.annotations[0].text == "api down"
        assert grid is None

    def test_autorender_registration(self, rates_page):
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "rates-chart.figure" in str(s["output"]))
        assert not spec["prevent_initial_call"]

    def test_every_control_is_an_input(self, rates_page):
        # Reactive page: all controls are Inputs, no Submit, no States.
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "rates-chart.figure" in str(s["output"]))
        inputs = str(spec["inputs"])
        for control in ("rates-series", "rates-first-date", "rates-last-date"):
            assert control in inputs
        assert "submit" not in inputs
        assert not spec["state"]

    def test_half_typed_date_prevents_update(self, rates_page, patched_rates):
        with pytest.raises(dash.exceptions.PreventUpdate):
            rates_page.update_rates_page(None, ["RUS_CBR.RATE"], "2010-", None)


class TestLayoutAndLink:
    def test_url_prefill_and_defaults(self, rates_page, mock_okama_symbols, null_cache):
        from pages.macro.macro_data import RATES_DEFAULTS

        page = rates_page.layout(tickers="RUS_CBR.RATE,FAKE.RATE")
        select = _find_by_id(page, "rates-series")
        assert select.value == ["RUS_CBR.RATE"]
        page_default = rates_page.layout()
        assert _find_by_id(page_default, "rates-series").value == RATES_DEFAULTS

    def test_link_callback(self, rates_page):
        link = rates_page.update_rates_link(1, "http://x/macro/rates", ["RUS_CBR.RATE"], "2010-01", "2024-12")
        assert link == "http://x/macro/rates?tickers=RUS_CBR.RATE&first_date=2010-01&last_date=2024-12"

    def test_export_guard(self, rates_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            rates_page.export_rates_stats(None, [{"property": "x"}])

    def test_empty_selection_disables_copy_link(self, rates_page):
        assert rates_page.disable_copy_link_rates([]) is True
        assert rates_page.disable_copy_link_rates(["RUS_CBR.RATE"]) is False


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

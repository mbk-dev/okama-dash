"""Page-level tests for /macro/inflation: main callback, auto-render registration,
overlay gating, URL prefill, link and export callbacks."""

from unittest.mock import patch

import dash
import plotly.graph_objects as go
import pytest

from tests.mocks.okama_mock import PicklableInflation, PicklableRate

pytestmark = pytest.mark.component


@pytest.fixture
def infl_page():
    from pages.macro import inflation

    return inflation


@pytest.fixture
def patched_objects(infl_page):
    with (
        patch.object(
            infl_page.macro_objects,
            "get_inflation_object",
            side_effect=lambda s, fd, ld: PicklableInflation(s),
        ),
        patch.object(
            infl_page.macro_objects,
            "get_rate_object",
            side_effect=lambda s, fd, ld: PicklableRate(s),
        ),
    ):
        yield


class TestMainCallback:
    def test_returns_figure_cards_and_grid(self, infl_page, patched_objects):
        fig, config, pp_cards, grid = infl_page.update_inflation_page(
            None, ["RUB.INFL", "USD.INFL"], "annual", [], "2000-01", "2026-05"
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert len(pp_cards.children) == 2
        assert grid.id == "infl-describe-table-grid"

    def test_overlay_on_adds_rate_traces(self, infl_page, patched_objects):
        fig, *_ = infl_page.update_inflation_page(
            None, ["RUB.INFL"], "rolling12m", ["on"], "2000-01", "2026-05"
        )
        assert len(fig.data) == 2  # 1 inflation line + 1 rate step-line
        assert fig.data[-1].line.shape == "hv"

    def test_overlay_ignored_for_cumulative(self, infl_page, patched_objects):
        fig, *_ = infl_page.update_inflation_page(
            None, ["RUB.INFL"], "cumulative", ["on"], "2000-01", "2026-05"
        )
        assert len(fig.data) == 1

    def test_purchasing_power_rows_dropped_from_grid(self, infl_page, patched_objects):
        *_, grid = infl_page.update_inflation_page(None, ["RUB.INFL"], "annual", [], None, None)
        properties = {row["property"] for row in grid.rowData}
        assert "1000 purchasing power" not in properties
        assert "compound inflation" in properties

    def test_empty_selection_prevents_update(self, infl_page):
        with pytest.raises(dash.exceptions.PreventUpdate):
            infl_page.update_inflation_page(None, [], "annual", [], None, None)

    def test_okama_error_renders_annotation_figure(self, infl_page):
        with patch.object(infl_page.macro_objects, "get_inflation_object", side_effect=ValueError("boom")):
            fig, config, pp_cards, grid = infl_page.update_inflation_page(
                None, ["RUB.INFL"], "annual", [], None, None
            )
        assert fig.layout.annotations[0].text == "boom"
        assert grid is None

    def test_half_typed_date_prevents_update(self, infl_page, patched_objects):
        # Reactive callbacks fire per keystroke in the date inputs; a partial
        # date must not reach okama.
        with pytest.raises(dash.exceptions.PreventUpdate):
            infl_page.update_inflation_page(None, ["RUB.INFL"], "annual", [], "202", None)


class TestReactiveWiring:
    def test_main_callback_fires_on_page_load(self, infl_page):
        # The chart must render without any click: the registration must NOT
        # suppress the initial call.
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "infl-chart.figure" in str(s["output"]))
        assert not spec["prevent_initial_call"]

    def test_every_control_is_an_input(self, infl_page):
        # Reactive page: changing any control recalculates immediately — all
        # controls are Inputs (no Submit button, no States).
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "infl-chart.figure" in str(s["output"]))
        inputs = str(spec["inputs"])
        for control in ("infl-series", "infl-plot-type", "infl-rates-overlay", "infl-first-date", "infl-last-date"):
            assert control in inputs
        assert "submit" not in inputs
        assert not spec["state"]


class TestLayout:
    def test_url_prefill_selects_known_symbols_only(self, infl_page, mock_okama_symbols, null_cache):
        page = infl_page.layout(tickers="RUB.INFL,FAKE.INFL", plot="monthly")
        select = _find_by_id(page, "infl-series")
        assert select.value == ["RUB.INFL"]
        plot = _find_by_id(page, "infl-plot-type")
        assert plot.value == "monthly"

    def test_default_layout_uses_catalog_defaults(self, infl_page, mock_okama_symbols, null_cache):
        from pages.macro.macro_data import INFLATION_DEFAULTS

        page = infl_page.layout()
        select = _find_by_id(page, "infl-series")
        assert select.value == INFLATION_DEFAULTS


class TestSecondaryCallbacks:
    def test_overlay_checkbox_disabled_for_non_overlay_plots(self, infl_page):
        options = infl_page.toggle_overlay_availability("cumulative")
        assert options[0]["disabled"] is True
        options = infl_page.toggle_overlay_availability("rolling12m")
        assert options[0]["disabled"] is False

    def test_link_callback_builds_macro_link(self, infl_page):
        link = infl_page.update_inflation_link(
            1, "http://x/macro/inflation", ["RUB.INFL"], "monthly", ["on"], "2010-01", "2024-12"
        )
        assert link.startswith("http://x/macro/inflation?tickers=RUB.INFL")
        assert "plot=monthly" in link
        assert "rates=true" in link
        assert "first_date=2010-01" in link

    def test_export_guard_prevents_autodownload(self, infl_page):
        # Dynamically rendered export buttons fire their callback on first
        # mount; n_clicks=None must not trigger a download (site-wide rule).
        with pytest.raises(dash.exceptions.PreventUpdate):
            infl_page.export_inflation_stats(None, [{"property": "x"}])

    def test_empty_selection_disables_copy_link(self, infl_page):
        # A copied "?tickers=" URL would be broken (no Submit button anymore —
        # the chart simply keeps its last state on empty selection).
        assert infl_page.disable_copy_link_inflation([]) is True
        assert infl_page.disable_copy_link_inflation(["RUB.INFL"]) is False


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

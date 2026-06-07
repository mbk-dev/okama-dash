"""Tests for /macro/cape10: history lines, snapshot bar of all 26 countries, callbacks."""

from unittest.mock import patch

import dash
import pandas as pd
import pytest

from tests.mocks.okama_mock import PicklableIndicator

pytestmark = pytest.mark.component


@pytest.fixture
def cape_page():
    from pages.macro import cape10

    return cape10


@pytest.fixture
def patched_indicator(cape_page):
    with patch.object(
        cape_page.macro_objects, "get_indicator_object", side_effect=lambda s, fd, ld: PicklableIndicator(s)
    ):
        yield


class TestHistoryFigure:
    def test_lines_with_country_names(self, cape_page):
        objects = [PicklableIndicator("USA_CAPE10.RATIO"), PicklableIndicator("RUS_CAPE10.RATIO")]
        fig = cape_page.get_cape_history_figure(objects)
        assert len(fig.data) == 2
        assert {t.name for t in fig.data} == {"USA", "Russia"}
        # CAPE is a raw decimal — no ×100 scaling
        assert max(fig.data[0].y) < 100


class TestSnapshot:
    def test_snapshot_collects_all_26_countries_sorted(self, cape_page, patched_indicator):
        with patch.object(cape_page, "get_or_create", side_effect=lambda **kw: (kw["constructor_fn"](), "k")):
            snapshot = cape_page.get_cape_snapshot()
        assert len(snapshot) == 26
        assert list(snapshot.index) == sorted(snapshot.index, key=lambda c: snapshot[c])

    def test_snapshot_figure_highlights_selected(self, cape_page):
        snapshot = pd.Series({"USA": 40.0, "Russia": 8.0, "Japan": 22.0}).sort_values()
        fig = cape_page.get_cape_snapshot_figure(snapshot, ["USA_CAPE10.RATIO"])
        bar = fig.data[0]
        assert bar.orientation == "h"
        colors = list(bar.marker.color)
        usa_pos = list(snapshot.index).index("USA")
        other_positions = [i for i in range(len(snapshot)) if i != usa_pos]
        assert all(colors[usa_pos] != colors[i] for i in other_positions)


class TestMainCallback:
    def test_history_mode(self, cape_page, patched_indicator):
        fig, config, grid = cape_page.update_cape_page(
            None, 0, ["USA_CAPE10.RATIO", "RUS_CAPE10.RATIO"], "history", "2000-01", "2026-05"
        )
        assert len(fig.data) == 2
        assert grid.id == "cape-describe-table-grid"

    def test_snapshot_mode_renders_bar(self, cape_page, patched_indicator):
        with patch.object(cape_page, "get_or_create", side_effect=lambda **kw: (kw["constructor_fn"](), "k")):
            fig, config, grid = cape_page.update_cape_page(
                None, 0, ["USA_CAPE10.RATIO"], "snapshot", None, None
            )
        assert fig.data[0].type == "bar"
        assert len(fig.data[0].y) == 26

    def test_decimal_formatter_in_grid(self, cape_page, patched_indicator):
        *_, grid = cape_page.update_cape_page(None, 0, ["USA_CAPE10.RATIO"], "history", None, None)
        value_col = next(d for d in grid.columnDefs if d["field"] == "USA_CAPE10.RATIO")
        assert value_col["valueFormatter"]["function"] == "formatDecimalGuarded(params.value)"

    def test_autorender_registration(self, cape_page):
        from dash._callback import GLOBAL_CALLBACK_LIST

        spec = next(s for s in GLOBAL_CALLBACK_LIST if "cape-chart.figure" in str(s["output"]))
        assert not spec["prevent_initial_call"]

    def test_error_renders_annotation(self, cape_page):
        with patch.object(cape_page.macro_objects, "get_indicator_object", side_effect=ValueError("nope")):
            fig, config, grid = cape_page.update_cape_page(None, 0, ["USA_CAPE10.RATIO"], "history", None, None)
        assert fig.layout.annotations[0].text == "nope"

    def test_empty_selection_prevents_update(self, cape_page):
        # Symmetry with the inflation/rates pages: the callback itself guards
        # against an empty selection, not only the disabled buttons.
        with pytest.raises(dash.exceptions.PreventUpdate):
            cape_page.update_cape_page(None, 0, [], "history", None, None)


class TestLayoutAndLink:
    def test_defaults_and_prefill(self, cape_page, mock_okama_symbols, null_cache):
        from pages.macro.macro_data import CAPE10_DEFAULTS

        assert _find_by_id(cape_page.layout(), "cape-series").value == CAPE10_DEFAULTS
        page = cape_page.layout(tickers="USA_CAPE10.RATIO", plot="snapshot")
        assert _find_by_id(page, "cape-plot-type").value == "snapshot"

    def test_link_callback(self, cape_page):
        link = cape_page.update_cape_link(
            1, "http://x/macro/cape10", ["USA_CAPE10.RATIO"], "snapshot", "2000-01", None
        )
        assert "plot=snapshot" in link

    def test_empty_selection_disables_submit_and_copy_link(self, cape_page):
        assert cape_page.disable_actions_cape([]) == (True, True)
        assert cape_page.disable_actions_cape(["USA_CAPE10.RATIO"]) == (False, False)


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

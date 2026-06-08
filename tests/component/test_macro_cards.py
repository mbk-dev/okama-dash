"""Wiring tests for the shared macro card factories (ids, defaults, reactive guards)."""

import pytest

from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_controls import (
    date_columns,
    dates_ready,
    make_submit_guard,
    series_multiselect_column,
)
from pages.macro.macro_data import INFLATION_SERIES

pytestmark = pytest.mark.component


def _collect_ids(component, acc=None):
    acc = acc if acc is not None else set()
    comp_id = getattr(component, "id", None)
    if isinstance(comp_id, str):
        acc.add(comp_id)
    children = getattr(component, "children", None)
    children = children if isinstance(children, list) else [children] if children is not None else []
    for child in children:
        _collect_ids(child, acc)
    return acc


class TestControlFactories:
    def test_series_multiselect_id_and_value(self):
        col = series_multiselect_column("infl", INFLATION_SERIES, ["RUB.INFL"])
        ids = _collect_ids(col)
        assert "infl-series" in ids
        select = next(c for c in iter_components(col) if getattr(c, "id", None) == "infl-series")
        assert select.value == ["RUB.INFL"]
        assert {"label": "Russia", "value": "RUB.INFL"} in select.data

    def test_date_columns_carry_page_prefix(self):
        cols = date_columns("cape", "2000-01", "2026-05")
        ids = set()
        for col in cols:
            ids |= _collect_ids(col)
        assert {"cape-first-date", "cape-last-date"} <= ids

    def test_submit_guard_disables_on_empty_selection(self):
        # Gates the Copy-link button on reactive macro pages.
        guard = make_submit_guard()
        assert guard([]) is True
        assert guard(None) is True
        assert guard(["RUB.INFL"]) is False


class TestDatesReady:
    def test_complete_or_empty_dates_pass(self):
        assert dates_ready("2000-01", "2026-05") is True
        assert dates_ready("", None) is True
        assert dates_ready("2000-01", "") is True

    def test_half_typed_date_blocks_recalculation(self):
        # Reactive callbacks fire per keystroke; "202" must not reach okama.
        assert dates_ready("202", "2026-05") is False
        assert dates_ready("2000-01", "2026-") is False
        assert dates_ready("20000-01", "2026-05") is False


class TestChartCard:
    def test_chart_card_id_and_classes(self):
        card = macro_chart_card("infl")
        assert "infl-chart" in _collect_ids(card)
        assert "chart-card" in card.class_name


class TestChartCardDownload:
    def test_chart_card_carries_download_block(self):
        from pages.macro.cards_macro.macro_chart import macro_chart_card

        ids = _collect_ids(macro_chart_card("infl"))
        assert {"infl-download-data-button", "infl-store-chart-data", "infl-download-xlsx"} <= ids


def iter_components(component):
    """Depth-first walk over a Dash component tree."""
    stack = [component]
    while stack:
        node = stack.pop()
        yield node
        children = getattr(node, "children", None)
        children = children if isinstance(children, list) else [children] if children is not None else []
        stack.extend(children)

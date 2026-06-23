"""The 'Last Date' default must reflect the current month at request time.

Regression for the stale module-level ``today_str`` bug: every dated controls
builder used to read ``today_str = pd.Timestamp.today()...`` captured once at
*import* time. A long-running Gunicorn worker that survived a month rollover
therefore defaulted Last Date to the month it was started in, silently
truncating the freshest month of data (observed live: an Efficient Frontier
ending 2026-05 while June data already existed).

Each builder must compute the current month per call. The test imports the page
module OUTSIDE the patch (so the buggy module-level constant is the real month,
not the faked future) and only the builder call runs under the patched clock —
otherwise a first-time import under the patch would make the buggy code look
correct.
"""

from unittest.mock import patch

import pandas as pd
import pytest

pytestmark = pytest.mark.component

FIXED_NOW = pd.Timestamp("2099-12-15")
EXPECTED_MONTH = "2099-12"


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        yield from _walk(child)


def _find(node, component_id):
    for item in _walk(node):
        if getattr(item, "id", None) == component_id:
            return item
    raise AssertionError(f"id {component_id!r} not found")


def _ef():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls

    return lambda: card_controls(None, None, None, None, None)


def _portfolio():
    from pages.portfolio.cards_portfolio.portfolio_controls import card_controls

    return lambda: card_controls(None, None, None, None, None, None, None, None, None, None)


def _compare():
    from pages.compare.cards_compare.asset_list_controls import card_controls

    return lambda: card_controls(None, None, None, None)


def _benchmark():
    from pages.benchmark.cards_benchmark.benchmark_controls import benchmark_card_controls

    return lambda: benchmark_card_controls(None, None, None, None, None)


def _macro_inflation():
    import pages.macro.inflation as page

    return page.layout


def _macro_real_estate():
    import pages.macro.real_estate as page

    return page.layout


CASES = [
    ("ef", _ef, "ef-last-date"),
    ("portfolio", _portfolio, "pf-last-date"),
    ("compare", _compare, "al-last-date"),
    ("benchmark", _benchmark, "benchmark-last-date"),
    ("macro_inflation", _macro_inflation, "infl-last-date"),
    ("macro_real_estate", _macro_real_estate, "re-last-date"),
]


@pytest.mark.parametrize("import_builder,input_id", [(c[1], c[2]) for c in CASES], ids=[c[0] for c in CASES])
def test_last_date_default_is_current_month_at_request_time(
    import_builder, input_id, mock_okama_symbols, null_cache
):
    # Import (and any module-level today_str) happens here, OUTSIDE the patch.
    build_layout = import_builder()
    with patch("pandas.Timestamp.today", return_value=FIXED_NOW):
        layout = build_layout()
    last_date_input = _find(layout, input_id)
    assert last_date_input.value == EXPECTED_MONTH

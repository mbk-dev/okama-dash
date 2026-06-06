"""
The chart's dcc.Loading spinner sits below the fold on mobile (tables push the
chart down), so each page's main data callback must also reveal a spinner under
its Submit button via the callback's `running` argument.
"""

import importlib

import pytest

pytestmark = pytest.mark.component

CASES = [
    ("pages.portfolio.portfolio", "pf-wealth-indexes.figure", "pf-submit-spinner"),
    ("pages.compare.compare", "al-wealth-indexes.figure", "al-submit-spinner"),
    ("pages.benchmark.benchmark", "benchmark-graph.figure", "benchmark-submit-spinner"),
    ("pages.efficient_frontier.frontier", "ef-graf.figure", "ef-submit-spinner"),
]


@pytest.mark.parametrize(("module", "output_key", "spinner_id"), CASES, ids=[c[2] for c in CASES])
def test_main_callback_toggles_submit_spinner_while_running(module, output_key, spinner_id):
    importlib.import_module(module)
    from dash._callback import GLOBAL_CALLBACK_LIST

    spec = next(s for s in GLOBAL_CALLBACK_LIST if output_key in s["output"])
    running = spec.get("running")
    assert running, f"main callback for {output_key} has no running spec"
    assert running["running"].get(f"{spinner_id}.style") == {"display": "block"}
    assert running["runningOff"].get(f"{spinner_id}.style") == {"display": "none"}

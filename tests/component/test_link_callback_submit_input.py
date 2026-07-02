"""Test that shareable-link callbacks fire on both Copy-link and Submit buttons.

The three main link callbacks (pf/al/benchmark) must have both the copy-link
button AND the submit button as Inputs so the Save-to-cabinet button works
right after Submit (without requiring a Copy-link click to populate the hidden
URL div).
"""
import pytest
from dash._callback import GLOBAL_CALLBACK_MAP

pytestmark = pytest.mark.component


def test_pf_link_callback_has_both_copy_and_submit_inputs(_dash_app):
    """Portfolio link callback fires on both pf-copy-link-button and pf-submit-button."""
    # Import to register the callback
    import pages.portfolio.cards_portfolio.portfolio_controls.links  # noqa: F401

    # Find the callback entry whose output is pf-show-url.children
    entry = None
    for _key, val in GLOBAL_CALLBACK_MAP.items():
        outputs = val["output"] if isinstance(val["output"], list) else [val["output"]]
        if any(o.component_id == "pf-show-url" and o.component_property == "children" for o in outputs):
            entry = val
            break

    assert entry is not None, "pf-show-url.children callback not found in registry"

    # Extract input ids
    input_ids = [inp["id"] for inp in entry["inputs"]]
    assert "pf-copy-link-button" in input_ids, "pf-copy-link-button input missing"
    assert "pf-submit-button" in input_ids, "pf-submit-button input missing"


def test_al_link_callback_has_both_copy_and_submit_inputs(_dash_app):
    """Compare (AssetList) link callback fires on both al-copy-link-button and al-submit-button."""
    import pages.compare.cards_compare.asset_list_controls  # noqa: F401

    entry = None
    for _key, val in GLOBAL_CALLBACK_MAP.items():
        outputs = val["output"] if isinstance(val["output"], list) else [val["output"]]
        if any(o.component_id == "al-show-url" and o.component_property == "children" for o in outputs):
            entry = val
            break

    assert entry is not None, "al-show-url.children callback not found in registry"

    input_ids = [inp["id"] for inp in entry["inputs"]]
    assert "al-copy-link-button" in input_ids, "al-copy-link-button input missing"
    assert "al-submit-button" in input_ids, "al-submit-button input missing"


def test_benchmark_link_callback_has_both_copy_and_submit_inputs(_dash_app):
    """Benchmark link callback fires on both benchmark-copy-link-button and benchmark-submit-button."""
    import pages.benchmark.cards_benchmark.benchmark_controls  # noqa: F401

    entry = None
    for _key, val in GLOBAL_CALLBACK_MAP.items():
        outputs = val["output"] if isinstance(val["output"], list) else [val["output"]]
        if any(
            o.component_id == "benchmark-show-url" and o.component_property == "children" for o in outputs
        ):
            entry = val
            break

    assert entry is not None, "benchmark-show-url.children callback not found in registry"

    input_ids = [inp["id"] for inp in entry["inputs"]]
    assert "benchmark-copy-link-button" in input_ids, "benchmark-copy-link-button input missing"
    assert "benchmark-submit-button" in input_ids, "benchmark-submit-button input missing"

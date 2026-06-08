"""Benchmark page accepts the pf_* URL portfolio group (issue #23).

The portfolio is a tested asset: it lands as a chip in benchmark-assets-list;
the benchmark select keeps its own param and default (SP500TR.INDX)."""

import pytest

pytestmark = pytest.mark.component

BENCHMARK_MODULE = "pages.benchmark.benchmark"

PF_DEF = {
    "tickers": ["AAPL.US", "MSFT.US"],
    "weights": [60.0, 40.0],
    "rebal": "year",
    "symbol": "MyPF.PF",
}


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


class TestBenchmarkLayoutPrefill:
    def test_store_and_chip_prefilled_benchmark_default_kept(self, mock_okama_symbols, null_cache):
        from pages.benchmark.benchmark import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60,40", pf_rebal="year", pf_symbol="MyPF")

        assert _find(page, "benchmark-url-portfolio").data == PF_DEF
        select = _find(page, "benchmark-assets-list")
        assert "MyPF.PF" in select.value
        assert {"value": "MyPF.PF", "label": "MyPF.PF"} in select.data
        assert _find(page, "select-benchmark").value == "SP500TR.INDX"

    def test_broken_group_renders_no_chip(self, mock_okama_symbols, null_cache):
        from pages.benchmark.benchmark import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60,60")  # sum != 100

        assert _find(page, "benchmark-url-portfolio").data is None
        assert _find(page, "benchmark-assets-list").value == []

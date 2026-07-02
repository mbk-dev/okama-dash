"""Benchmark page accepts the pf_* URL portfolio group (issue #23).

The portfolio is a tested asset: it lands as a chip in benchmark-assets-list;
the benchmark select keeps its own param and default (SP500TR.INDX)."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.component

BENCHMARK_MODULE = "pages.benchmark.benchmark"

PF_DEF = {
    "tickers": ["AAPL.US", "MSFT.US"],
    "weights": [60.0, 40.0],
    "rebal": "year",
    "symbol": "MyPF.PF",
    "abs_dev": None,
    "rel_dev": None,
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


class TestBenchmarkSearchInjection:
    def test_portfolio_option_injected_while_store_present(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark.benchmark_controls import optimize_search_assets_benchmark

        options = optimize_search_assets_benchmark("AAP", ["MyPF.PF"], PF_DEF)
        assert {"value": "MyPF.PF", "label": "MyPF.PF"} in options

    def test_no_injection_without_store(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark.benchmark_controls import optimize_search_assets_benchmark

        options = optimize_search_assets_benchmark("AAP", [], None)
        assert all(option["value"] != "MyPF.PF" for option in options)


class TestBenchmarkCopyLinkRoundTrip:
    def test_link_carries_pf_group_and_benchmark(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark.benchmark_controls import update_link_benchmark

        link = update_link_benchmark(
            1,
            1,
            "https://okama.io/benchmark",
            "SP500TR.INDX",
            ["MyPF.PF", "GOOG.US"],
            "EUR",
            "2015-01",
            "2020-12",
            PF_DEF,
        )
        assert "benchmark=SP500TR.INDX" in link
        assert "tickers=GOOG.US" in link
        assert "pf_tickers=AAPL.US,MSFT.US" in link
        assert "pf_weights=60,40" in link
        assert "pf_rebal=year" in link
        assert "pf_symbol=MyPF.PF" in link

    def test_chip_removed_emits_plain_link(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark.benchmark_controls import update_link_benchmark

        link = update_link_benchmark(
            1, 1, "https://okama.io/benchmark", "SP500TR.INDX", ["GOOG.US"], "EUR", "2015-01", "2020-12", PF_DEF
        )
        assert "pf_tickers" not in link


class TestBenchmarkInfoTokenFilter:
    def test_info_panel_filters_chip(self, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark import benchmark_info

        with (
            patch("pages.benchmark.cards_benchmark.benchmark_info.ok.AssetList") as mock_al_cls,
            patch("common.html_elements.info_ag_grid.get_assets_names", return_value="names"),
            patch("common.html_elements.info_ag_grid.get_info", return_value="info"),
        ):
            benchmark_info.pf_update_asset_names_info(["MyPF.PF", "AAPL.US"], "SP500TR.INDX", "USD", PF_DEF)

        assert mock_al_cls.call_args.args[0] == ["SP500TR.INDX", "AAPL.US"]


class TestBenchmarkMainCallbackWithPortfolio:
    @staticmethod
    def _run(selected_symbols, pf_def):
        from pages.benchmark.benchmark import update_graf_benchmark
        from tests.mocks.okama_mock import make_mock_asset_list

        pf_object = MagicMock()
        pf_object.symbol = "MyPF.PF"
        al = make_mock_asset_list(["SP500TR.INDX", "MyPF.PF"])
        captured = {}

        def fake_get_or_create(*, obj_type, constructor_fn, cache_key_params, ttl_seconds):
            captured["cache_key_params"] = cache_key_params
            return constructor_fn(), "test.pkl"

        with (
            patch("pages.benchmark.benchmark.get_or_create", side_effect=fake_get_or_create),
            patch("pages.benchmark.benchmark.get_or_create_url_portfolio", return_value=pf_object) as mock_pf,
            patch("pages.benchmark.benchmark.ok.AssetList", return_value=al) as mock_al_cls,
        ):
            update_graf_benchmark(
                None,  # screen
                1,  # n_clicks
                "SP500TR.INDX",
                selected_symbols,
                "USD",
                "2020-01",
                "2024-12",
                "annualized_td",
                "expanding",
                2,
                pf_def,
            )
        return mock_pf, mock_al_cls, captured

    def test_benchmark_stays_first_portfolio_second(self):
        mock_pf, mock_al_cls, captured = self._run(["MyPF.PF"], PF_DEF)

        mock_pf.assert_called_once_with(PF_DEF, ccy="USD", first_date="2020-01", last_date="2024-12")
        symbols = mock_al_cls.call_args.args[0]
        assert symbols[0] == "SP500TR.INDX"
        assert symbols[1] is mock_pf.return_value
        assert captured["cache_key_params"]["symbols"] == ["SP500TR.INDX"]
        assert captured["cache_key_params"]["pf"] == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"

    def test_without_chip_nothing_changes(self):
        mock_pf, mock_al_cls, captured = self._run(["GOOG.US"], PF_DEF)

        mock_pf.assert_not_called()
        assert mock_al_cls.call_args.args[0] == ["SP500TR.INDX", "GOOG.US"]
        assert captured["cache_key_params"]["pf"] is None

    def test_deviations_flow_to_portfolio_builder(self):
        pf_def = dict(PF_DEF, abs_dev=5.0, rel_dev=10.0)
        mock_pf, mock_al_cls, captured = self._run(["MyPF.PF"], pf_def)
        mock_pf.assert_called_once_with(pf_def, ccy="USD", first_date="2020-01", last_date="2024-12")
        assert captured["cache_key_params"]["pf"] == "AAPL.US:60,MSFT.US:40;year;MyPF.PF;5;10"

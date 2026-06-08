"""Compare page accepts the pf_* URL portfolio group (issue #23).

The portfolio arrives as its own param group, shows up as a synthetic chip in
the tickers MultiSelect, joins the AssetList on Submit, and round-trips
through the page's copy-link.
"""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.component

COMPARE_MODULE = "pages.compare.compare"

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


class TestCompareLayoutPrefill:
    def test_store_and_chip_prefilled(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60,40", pf_rebal="year", pf_symbol="MyPF")

        assert _find(page, "al-url-portfolio").data == PF_DEF
        select = _find(page, "al-symbols-list")
        assert "MyPF.PF" in select.value
        assert {"value": "MyPF.PF", "label": "MyPF.PF"} in select.data

    def test_chip_coexists_with_page_tickers(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(tickers="GOOG.US", pf_tickers="AAPL.US,MSFT.US", pf_weights="60,40")

        select = _find(page, "al-symbols-list")
        assert select.value == ["PORTFOLIO.PF", "GOOG.US"]

    def test_broken_group_renders_no_chip(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(pf_tickers="AAPL.US,MSFT.US", pf_weights="60")  # length mismatch

        assert _find(page, "al-url-portfolio").data is None
        select = _find(page, "al-symbols-list")
        assert select.value == []

    def test_plain_link_has_store_with_none(self, mock_okama_symbols, null_cache):
        from pages.compare.compare import layout

        page = layout(tickers="AAPL.US,MSFT.US")

        assert _find(page, "al-url-portfolio").data is None


class TestCompareSearchInjection:
    def test_portfolio_option_injected_while_store_present(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import optimize_search_al

        options = optimize_search_al("AAP", ["MyPF.PF"], PF_DEF)
        assert {"value": "MyPF.PF", "label": "MyPF.PF"} in options

    def test_no_injection_without_store(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import optimize_search_al

        options = optimize_search_al("AAP", [], None)
        assert all(option["value"] != "MyPF.PF" for option in options)


class TestCompareCopyLinkRoundTrip:
    def test_link_carries_pf_group_and_remaining_tickers(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import update_link_al

        link = update_link_al(
            1, "https://okama.io/compare", ["MyPF.PF", "GOOG.US"], "EUR", "2015-01", "2020-12", PF_DEF
        )
        assert "tickers=GOOG.US" in link
        assert "pf_tickers=AAPL.US,MSFT.US" in link
        assert "pf_weights=60,40" in link
        assert "pf_rebal=year" in link
        assert "pf_symbol=MyPF.PF" in link

    def test_default_symbol_omitted_from_link(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import update_link_al

        pf_def = dict(PF_DEF, symbol="PORTFOLIO.PF")
        link = update_link_al(1, "https://okama.io/compare", ["PORTFOLIO.PF"], "EUR", "2015-01", "2020-12", pf_def)
        assert "pf_symbol=" not in link
        assert "pf_tickers=AAPL.US,MSFT.US" in link

    def test_chip_removed_emits_plain_link(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import update_link_al

        link = update_link_al(1, "https://okama.io/compare", ["GOOG.US"], "EUR", "2015-01", "2020-12", PF_DEF)
        assert "pf_tickers" not in link
        assert "tickers=GOOG.US" in link


class TestCompareEfLinkTokenExclusion:
    def test_ef_link_excludes_chip(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import update_link_to_ef

        link = update_link_to_ef(["MyPF.PF", "AAPL.US", "MSFT.US"], "USD", "2015-01", "2020-12", PF_DEF)
        assert "tickers=AAPL.US,MSFT.US" in link
        assert "MyPF.PF" not in link

    def test_ef_disable_counts_real_tickers_only(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare.asset_list_controls import disable_ef_link_button

        # chip + 1 real ticker -> 1 real ticker -> EF link disabled
        assert disable_ef_link_button(["MyPF.PF", "AAPL.US"], PF_DEF) is True
        # chip + 2 real tickers -> enabled
        assert disable_ef_link_button(["MyPF.PF", "AAPL.US", "MSFT.US"], PF_DEF) is False


class TestCompareAssetsInfoTokenFilter:
    def test_info_panel_filters_chip(self, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare import assets_info

        with (
            patch("pages.compare.cards_compare.assets_info.ok.AssetList") as mock_al_cls,
            patch("pages.compare.cards_compare.assets_info.get_assets_names", return_value="names"),
            patch("pages.compare.cards_compare.assets_info.get_info", return_value="info"),
        ):
            assets_info.pf_update_asset_names_info(["MyPF.PF", "AAPL.US"], "USD", False, PF_DEF)

        assert mock_al_cls.call_args.args[0] == ["AAPL.US"]

    def test_chip_only_prevents_update(self, mock_okama_symbols, null_cache):
        import dash.exceptions

        from pages.compare.cards_compare import assets_info

        with pytest.raises(dash.exceptions.PreventUpdate):
            assets_info.pf_update_asset_names_info(["MyPF.PF"], "USD", False, PF_DEF)


class TestCompareMainCallbackWithPortfolio:
    @staticmethod
    def _run_inner(selected_symbols, pf_def):
        from pages.compare.compare import _update_graf_compare_inner
        from tests.mocks.okama_mock import make_mock_asset_list

        pf_object = MagicMock()
        pf_object.symbol = "MyPF.PF"
        al = make_mock_asset_list(["MyPF.PF", "GOOG.US"])
        captured = {}

        def fake_get_or_create(*, obj_type, constructor_fn, cache_key_params, ttl_seconds):
            captured["cache_key_params"] = cache_key_params
            return constructor_fn(), "test.pkl"

        with (
            patch("pages.compare.compare.get_or_create", side_effect=fake_get_or_create),
            patch("pages.compare.compare.get_or_create_url_portfolio", return_value=pf_object) as mock_pf,
            patch("pages.compare.compare.ok.AssetList", return_value=al) as mock_al_cls,
        ):
            _update_graf_compare_inner(
                screen=None,
                log_on=False,
                selected_symbols=selected_symbols,
                ccy="USD",
                fd_value="2020-01",
                ld_value="2024-12",
                plot_type="wealth",
                inflation_on=False,
                rolling_window=2,
                pf_def=pf_def,
            )
        return mock_pf, mock_al_cls, captured

    def test_portfolio_object_joins_assetlist_and_cache_key(self):
        mock_pf, mock_al_cls, captured = self._run_inner(["MyPF.PF", "GOOG.US"], PF_DEF)

        mock_pf.assert_called_once_with(PF_DEF, ccy="USD", first_date="2020-01", last_date="2024-12")
        assets = mock_al_cls.call_args.args[0]
        assert assets[0] is mock_pf.return_value
        assert assets[1:] == ["GOOG.US"]
        assert captured["cache_key_params"]["symbols"] == ["GOOG.US"]
        assert captured["cache_key_params"]["pf"] == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"

    def test_without_chip_nothing_changes(self):
        mock_pf, mock_al_cls, captured = self._run_inner(["GOOG.US"], PF_DEF)

        mock_pf.assert_not_called()
        assert mock_al_cls.call_args.args[0] == ["GOOG.US"]
        assert captured["cache_key_params"]["pf"] is None

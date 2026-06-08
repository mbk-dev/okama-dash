import pandas as pd
import pytest

pytestmark = pytest.mark.component

ARGS = (["AAPL.US", "MSFT.US"], [60, 40], "EUR", "2015-01", "2020-12", "year", "MyPF")


class TestGoToLinks:
    def _links(self, *args):
        from pages.portfolio.cards_portfolio.portfolio_controls import update_go_to_links

        return update_go_to_links(*args)

    def test_ef_link_keeps_page_level_vocabulary(self):
        ef, _, _ = self._links(*ARGS)
        assert ef.startswith("/?tickers=AAPL.US,MSFT.US")
        assert "weights=60,40" in ef
        assert "symbol=MyPF" in ef
        assert "rebal=year" in ef
        assert "ccy=EUR" in ef
        assert "first_date=2015-01" in ef
        assert "last_date=2020-12" in ef
        # Guard against splatting the handoff dict into the EF call: none of the
        # pf_* group must leak into the page-level EF link.
        assert "pf_tickers" not in ef
        assert "pf_weights" not in ef
        assert "pf_symbol" not in ef

    def test_compare_link_carries_pf_group_only(self):
        _, compare, _ = self._links(*ARGS)
        assert compare.startswith("/compare?")
        assert "pf_tickers=AAPL.US,MSFT.US" in compare
        assert "pf_weights=60,40" in compare
        assert "pf_rebal=year" in compare
        assert "pf_symbol=MyPF" in compare
        assert "ccy=EUR" in compare
        # No page-level tickers/weights, no cash-flow params, no benchmark.
        assert "?tickers=" not in compare
        assert "&tickers=" not in compare
        assert "&weights=" not in compare
        assert "cf_" not in compare
        assert "initial_amount" not in compare
        assert "benchmark=" not in compare

    def test_benchmark_link_same_group_default_benchmark_kept(self):
        _, compare, benchmark = self._links(*ARGS)
        assert benchmark.startswith("/benchmark?")
        assert benchmark.split("?", 1)[1] == compare.split("?", 1)[1]
        assert "benchmark=" not in benchmark

    def test_defaults_omitted_in_handoff_links(self):
        today_str = pd.Timestamp.today().strftime("%Y-%m")
        _, compare, _ = self._links(
            ["AAPL.US", "MSFT.US"], [50, 50], "USD", "2000-01", today_str, "month", "PORTFOLIO"
        )
        assert "pf_rebal=" not in compare
        assert "pf_symbol=" not in compare
        assert "ccy=" not in compare
        assert "first_date=" not in compare
        assert "last_date=" not in compare
        assert "pf_weights=50,50" in compare

    def test_empty_rows_skipped(self):
        ef, compare, _ = self._links(
            ["AAPL.US", "MSFT.US", None], [60, 40, None], "EUR", "2015-01", "2020-12", "year", None
        )
        assert "tickers=AAPL.US,MSFT.US" in ef
        assert "pf_tickers=AAPL.US,MSFT.US" in compare
        assert "pf_weights=60,40" in compare


class TestGoToMenuGating:
    def test_enabled_on_valid_two_asset_portfolio(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import (
            disable_submit_add_link_buttons,
        )

        *_, go_disabled = disable_submit_add_link_buttons(
            ["AAPL.US", "MSFT.US"],
            [60, 40],
            12,
            True,
            True,
        )
        assert go_disabled is False

    def test_disabled_with_single_ticker(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import (
            disable_submit_add_link_buttons,
        )

        *_, go_disabled = disable_submit_add_link_buttons(["AAPL.US"], [100], 12, True, True)
        assert go_disabled is True

    def test_disabled_when_weights_do_not_sum_to_100(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import (
            disable_submit_add_link_buttons,
        )

        *_, go_disabled = disable_submit_add_link_buttons(
            ["AAPL.US", "MSFT.US"],
            [60, 60],
            12,
            True,
            True,
        )
        assert go_disabled is True


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


class TestGoToMenuMarkup:
    def test_menu_replaces_button_with_three_link_items(self, mock_okama_symbols, null_cache):
        import dash_bootstrap_components as dbc

        from pages.portfolio.cards_portfolio.portfolio_controls import card_controls

        card = card_controls(None, None, None, None, None, None, None, None, None, None)

        menu = _find(card, "pf-goto-menu")
        assert isinstance(menu, dbc.DropdownMenu)
        item_ids = [getattr(item, "id", None) for item in menu.children]
        assert item_ids == ["pf-goto-ef", "pf-goto-compare", "pf-goto-benchmark"]
        for item in menu.children:
            assert item.external_link is True
            assert item.target == "_blank"
        with pytest.raises(AssertionError):
            _find(card, "pf-go-to-ef-button")

import pandas as pd
import pytest

pytestmark = pytest.mark.component


class TestGoToEfLink:
    def test_link_contains_tickers_weights_symbol_rebal_ccy(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import update_go_to_ef_link

        link = update_go_to_ef_link(
            ["AAPL.US", "MSFT.US"],
            [60, 40],
            "EUR",
            "2015-01",
            "2020-12",
            "year",
            "MyPF",
        )

        assert link.startswith("/?tickers=AAPL.US,MSFT.US")
        assert "weights=60,40" in link
        assert "symbol=MyPF" in link
        assert "rebal=year" in link
        assert "ccy=EUR" in link
        assert "first_date=2015-01" in link
        assert "last_date=2020-12" in link

    def test_link_omits_defaults(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import update_go_to_ef_link

        today_str = pd.Timestamp.today().strftime("%Y-%m")
        link = update_go_to_ef_link(
            ["AAPL.US", "MSFT.US"],
            [50, 50],
            "USD",
            "2000-01",
            today_str,
            "month",
            "PORTFOLIO",
        )

        assert "ccy=" not in link
        assert "symbol=" not in link
        assert "rebal=" not in link
        assert "first_date=" not in link
        assert "last_date=" not in link
        assert "weights=50,50" in link

    def test_link_skips_empty_rows(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import update_go_to_ef_link

        link = update_go_to_ef_link(
            ["AAPL.US", "MSFT.US", None],
            [60, 40, None],
            "EUR",
            "2015-01",
            "2020-12",
            "year",
            None,
        )

        assert "tickers=AAPL.US,MSFT.US" in link
        assert "weights=60,40" in link


class TestGoToEfGating:
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

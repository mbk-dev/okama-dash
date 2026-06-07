"""Unit tests for common/url_portfolio.py (issue #23).

The pf_* URL group hands a bare rebalanced portfolio from the Portfolio page
to Compare/Benchmark. The parser mirrors the EF handoff validation; the split
helper is the single chip-recognition point for every consumer of a tickers
MultiSelect value list.
"""

import pytest

from common.url_portfolio import (
    parse_url_portfolio_group,
    pf_cache_token,
    pf_link_kwargs,
    portfolio_option,
    split_portfolio_from_selection,
)

pytestmark = pytest.mark.unit

PF_DEF = {
    "tickers": ["AAPL.US", "MSFT.US"],
    "weights": [60.0, 40.0],
    "rebal": "year",
    "symbol": "MyPF.PF",
}


class TestParseUrlPortfolioGroup:
    def test_valid_group_parses_with_defaults(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", None, None)
        assert result == {
            "tickers": ["AAPL.US", "MSFT.US"],
            "weights": [60.0, 40.0],
            "rebal": "month",
            "symbol": "PORTFOLIO.PF",
        }

    def test_symbol_normalized_spaces_and_suffix(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", "year", "My PF")
        assert result["symbol"] == "My_PF.PF"
        assert result["rebal"] == "year"

    def test_symbol_with_pf_suffix_kept(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", None, "MyPF.PF")
        assert result["symbol"] == "MyPF.PF"

    def test_absent_group_returns_none(self):
        assert parse_url_portfolio_group(None, None, None, None) is None

    def test_weights_without_tickers_return_none(self):
        assert parse_url_portfolio_group(None, "60,40", None, None) is None

    def test_length_mismatch_returns_none(self):
        assert parse_url_portfolio_group("AAPL.US,MSFT.US", "60", None, None) is None

    def test_sum_not_100_returns_none(self):
        assert parse_url_portfolio_group("AAPL.US,MSFT.US", "60,60", None, None) is None

    def test_non_numeric_weights_return_none(self):
        assert parse_url_portfolio_group("AAPL.US,MSFT.US", "60,abc", None, None) is None


class TestSplitPortfolioFromSelection:
    def test_token_split_out(self):
        tickers, has_pf = split_portfolio_from_selection(["MyPF.PF", "SPY.US"], PF_DEF)
        assert tickers == ["SPY.US"]
        assert has_pf is True

    def test_no_token_in_values(self):
        tickers, has_pf = split_portfolio_from_selection(["SPY.US"], PF_DEF)
        assert tickers == ["SPY.US"]
        assert has_pf is False

    def test_none_pf_def(self):
        assert split_portfolio_from_selection(["SPY.US"], None) == (["SPY.US"], False)

    def test_none_values(self):
        assert split_portfolio_from_selection(None, PF_DEF) == ([], False)

    def test_none_entries_dropped(self):
        tickers, has_pf = split_portfolio_from_selection([None, "MyPF.PF"], PF_DEF)
        assert tickers == []
        assert has_pf is True


class TestPortfolioOption:
    def test_option_dict(self):
        assert portfolio_option(PF_DEF) == {"value": "MyPF.PF", "label": "MyPF.PF"}


class TestPfLinkKwargs:
    def test_custom_symbol_kept(self):
        assert pf_link_kwargs(PF_DEF) == {
            "pf_tickers": ["AAPL.US", "MSFT.US"],
            "pf_weights": [60.0, 40.0],
            "pf_rebal": "year",
            "pf_symbol": "MyPF.PF",
        }

    def test_default_symbol_omitted(self):
        pf_def = dict(PF_DEF, symbol="PORTFOLIO.PF")
        assert pf_link_kwargs(pf_def)["pf_symbol"] is None


class TestPfCacheToken:
    def test_token_format(self):
        assert pf_cache_token(PF_DEF) == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"

    def test_none_for_absent_def(self):
        assert pf_cache_token(None) is None

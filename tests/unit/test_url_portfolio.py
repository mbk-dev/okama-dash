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
    "abs_dev": None,
    "rel_dev": None,
}


class TestParseUrlPortfolioGroup:
    def test_valid_group_parses_with_defaults(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", None, None)
        assert result == {
            "tickers": ["AAPL.US", "MSFT.US"],
            "weights": [60.0, 40.0],
            "rebal": "month",
            "symbol": "PORTFOLIO.PF",
            "abs_dev": None,
            "rel_dev": None,
        }

    def test_deviations_parsed(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", "year", "MyPF", "5", "10")
        assert result["abs_dev"] == 5.0
        assert result["rel_dev"] == 10.0

    def test_bad_deviation_ignored(self):
        result = parse_url_portfolio_group("AAPL.US,MSFT.US", "60,40", None, None, "abc", "")
        assert result["abs_dev"] is None
        assert result["rel_dev"] is None

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
            "pf_abs_dev": None,
            "pf_rel_dev": None,
        }

    def test_default_symbol_omitted(self):
        pf_def = dict(PF_DEF, symbol="PORTFOLIO.PF")
        assert pf_link_kwargs(pf_def)["pf_symbol"] is None

    def test_link_kwargs_carry_deviations(self):
        pf_def = dict(PF_DEF, abs_dev=5.0, rel_dev=10.0)
        kw = pf_link_kwargs(pf_def)
        assert kw["pf_abs_dev"] == 5.0
        assert kw["pf_rel_dev"] == 10.0


class TestPfCacheToken:
    def test_token_format(self):
        assert pf_cache_token(PF_DEF) == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"

    def test_token_includes_deviations_when_present(self):
        pf_def = dict(PF_DEF, abs_dev=5.0, rel_dev=10.0)
        assert pf_cache_token(pf_def) == "AAPL.US:60,MSFT.US:40;year;MyPF.PF;5;10"

    def test_token_unchanged_without_deviations(self):
        assert pf_cache_token(PF_DEF) == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"

    def test_none_for_absent_def(self):
        assert pf_cache_token(None) is None

    def test_token_is_path_safe(self):
        # A crafted pf_symbol must not smuggle path separators into the
        # cache filename (object_cache interpolates the token verbatim).
        pf_def = dict(PF_DEF, symbol="a/b.PF", tickers=["AA/PL.US", "MSFT.US"])
        token = pf_cache_token(pf_def)
        assert "/" not in token
        assert token == "AA_PL.US:60,MSFT.US:40;year;a_b.PF"


class TestGetOrCreateUrlPortfolio:
    def test_wires_object_cache(self):
        from unittest.mock import MagicMock, patch

        import common.url_portfolio as up

        sentinel = MagicMock()
        with patch.object(up, "get_or_create", return_value=(sentinel, "k.pkl")) as goc:
            result = up.get_or_create_url_portfolio(PF_DEF, ccy="EUR", first_date="2015-01", last_date="2020-12")

        assert result is sentinel
        kwargs = goc.call_args.kwargs
        assert kwargs["obj_type"] == "portfolio"
        assert kwargs["ttl_seconds"] == up.TTL_PORTFOLIO
        key = kwargs["cache_key_params"]
        assert key["ccy"] == "EUR"
        assert key["first_date"] == "2015-01"
        assert key["last_date"] == "2020-12"
        # Sanitized single discriminator — raw URL strings must not reach the
        # pickle filename (see pf_cache_token).
        assert key["pf"] == "AAPL.US:60,MSFT.US:40;year;MyPF.PF"
        assert key["purpose"] == "url_portfolio"
        assert "symbols" not in key
        assert "symbol" not in key
        assert "weights" not in key

    def test_constructor_builds_portfolio(self):
        from unittest.mock import patch

        import common.url_portfolio as up

        def run_constructor(*, obj_type, constructor_fn, cache_key_params, ttl_seconds):
            return constructor_fn(), "k.pkl"

        with (
            patch.object(up, "get_or_create", side_effect=run_constructor),
            patch.object(up.ok, "Portfolio") as mock_pf,
            patch.object(up.ok, "Rebalance") as mock_rebal,
        ):
            up.get_or_create_url_portfolio(PF_DEF, ccy="EUR", first_date="2015-01", last_date="2020-12")

        mock_rebal.assert_called_once_with(period="year", abs_deviation=None, rel_deviation=None)
        mock_pf.assert_called_once_with(
            assets=["AAPL.US", "MSFT.US"],
            weights=[0.6, 0.4],
            ccy="EUR",
            first_date="2015-01",
            last_date="2020-12",
            inflation=False,
            rebalancing_strategy=mock_rebal.return_value,
            symbol="MyPF.PF",
        )

    def test_constructor_builds_portfolio_with_deviations(self):
        from unittest.mock import patch

        import common.url_portfolio as up

        def run_constructor(*, obj_type, constructor_fn, cache_key_params, ttl_seconds):
            return constructor_fn(), "k.pkl"

        pf_def = dict(PF_DEF, abs_dev=5.0, rel_dev=10.0)
        with (
            patch.object(up, "get_or_create", side_effect=run_constructor),
            # ok.Portfolio is patched so _construct() doesn't build a real one;
            # the assertion is on the Rebalance the constructor passes to it.
            patch.object(up.ok, "Portfolio"),
            patch.object(up.ok, "Rebalance") as mock_rebal,
        ):
            up.get_or_create_url_portfolio(pf_def, ccy="EUR", first_date="2015-01", last_date="2020-12")

        mock_rebal.assert_called_once_with(period="year", abs_deviation=0.05, rel_deviation=0.10)

import pytest

pytestmark = pytest.mark.component


class TestParseUrlPortfolio:
    def test_valid_section_parsed(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        result = _parse_url_portfolio(["SPY.US", "BND.US"], "60,40", "MyPF")

        assert result == {
            "tickers": ["SPY.US", "BND.US"],
            "weights": [60.0, 40.0],
            "symbol": "MyPF",
        }

    def test_none_when_weights_missing(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], None, None) is None

    def test_none_when_weights_unparseable(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,abc", None) is None

    def test_none_when_count_mismatch(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,30,10", None) is None

    def test_none_when_sum_not_100(self):
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,30", None) is None

    def test_none_when_weights_contain_empty_field(self):
        # "60," parses to [60.0, nan]; the NaN sum must not slip through the
        # tolerance check (NaN comparisons are False both ways).
        from pages.efficient_frontier.frontier import _parse_url_portfolio

        assert _parse_url_portfolio(["SPY.US", "BND.US"], "60,", None) is None

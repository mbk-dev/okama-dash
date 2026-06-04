import pytest

pytestmark = pytest.mark.unit


class TestBuildDistributionParameters:
    def test_norm_returns_mu_sigma_floats(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        result = build_distribution_parameters("norm", "0.007", "0.04", None, None, None, None, None)
        assert result == (0.007, 0.04)

    def test_norm_all_empty_returns_none(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        assert build_distribution_parameters("norm", None, "", None, None, None, None, None) is None

    def test_lognorm_forces_loc_minus_one(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        result = build_distribution_parameters("lognorm", None, None, "0.05", "1.01", None, None, None)
        assert result == (0.05, -1.0, 1.01)

    def test_lognorm_only_shape_keeps_scale_none(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        result = build_distribution_parameters("lognorm", None, None, "0.05", None, None, None, None)
        assert result == (0.05, -1.0, None)

    def test_lognorm_all_empty_returns_none(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        assert build_distribution_parameters("lognorm", None, None, None, "", None, None, None) is None

    def test_t_returns_df_loc_scale(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        result = build_distribution_parameters("t", None, None, None, None, "3.4", "0.006", "0.038")
        assert result == (3.4, 0.006, 0.038)

    def test_t_all_empty_returns_none(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        assert build_distribution_parameters("t", None, None, None, None, None, None, None) is None

    def test_unknown_distribution_returns_none(self):
        from pages.portfolio.portfolio import build_distribution_parameters

        assert build_distribution_parameters("weird", "1", "2", None, None, None, None, None) is None


class TestPortfolioIsComplete:
    def test_complete_portfolio_is_true(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete(["AAPL.US", "MSFT.US"], [50, 50]) is True

    def test_float_weights_within_tolerance(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete(["A.US", "B.US", "C.US"], [33.3, 33.3, 33.4]) is True

    def test_sum_not_100_is_false(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete(["AAPL.US", "MSFT.US"], [50, 40]) is False

    def test_missing_ticker_is_false(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete([None, "MSFT.US"], [50, 50]) is False

    def test_missing_weight_is_false(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete(["AAPL.US", "MSFT.US"], [50, None]) is False

    def test_empty_lists_are_false(self):
        from pages.portfolio.portfolio import _portfolio_is_complete

        assert _portfolio_is_complete([], []) is False


class TestValidMcDate:
    def test_empty_and_none_are_valid(self):
        from pages.portfolio.portfolio import _valid_mc_date

        assert _valid_mc_date(None) is True
        assert _valid_mc_date("") is True

    def test_yyyy_mm_is_valid(self):
        from pages.portfolio.portfolio import _valid_mc_date

        assert _valid_mc_date("2020-01") is True

    def test_partial_dates_are_invalid(self):
        from pages.portfolio.portfolio import _valid_mc_date

        assert _valid_mc_date("202") is False
        assert _valid_mc_date("2020-1") is False

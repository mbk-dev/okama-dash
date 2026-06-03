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

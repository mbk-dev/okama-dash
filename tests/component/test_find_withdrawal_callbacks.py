"""Find max withdrawal block (issue #22): collapse + target-survival-period visibility."""

import pytest

pytestmark = pytest.mark.component


class TestToggleFindCollapse:
    def test_opens_from_closed_with_down_chevron(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_find_collapse

        assert toggle_find_collapse(1, False) == (True, "bi bi-chevron-down me-2")

    def test_closes_from_open_with_right_chevron(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_find_collapse

        assert toggle_find_collapse(2, True) == (False, "bi bi-chevron-right me-2")


class TestToggleFindTargetSp:
    def test_survival_goal_shows_input(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_find_target_sp

        assert toggle_find_target_sp("survival_period") is None

    def test_maintain_pv_hides_input(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_find_target_sp

        assert toggle_find_target_sp("maintain_balance_pv") == {"display": "none"}

    def test_maintain_fv_hides_input(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_find_target_sp

        assert toggle_find_target_sp("maintain_balance_fv") == {"display": "none"}


class TestStrategyPanelsHideFindBlock:
    def test_time_series_hides_find_block(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_strategy_panels

        result = toggle_strategy_panels("time_series")
        assert len(result) == 6  # description + 4 panel styles + find block
        assert result[5] == {"display": "none"}

    @pytest.mark.parametrize("strategy", ["indexation", "percentage", "vds", "cwd"])
    def test_supported_strategies_show_find_block(self, strategy):
        from pages.portfolio.cards_portfolio.cashflow_controls import toggle_strategy_panels

        assert toggle_strategy_panels(strategy)[5] is None


class TestValidateFindInputs:
    def _validate(self, percentile, target_sp, mc_years):
        from pages.portfolio.cards_portfolio.cashflow_controls import validate_find_inputs

        return validate_find_inputs(percentile, target_sp, mc_years)

    def test_defaults_are_valid(self):
        assert self._validate(20, 25, 30) == (False, False)

    def test_percentile_out_of_range_string_is_invalid(self):
        # out-of-range typed values arrive from dcc as strings (same as MC inputs)
        assert self._validate("150", 25, 30)[0] is True

    def test_percentile_none_is_invalid(self):
        assert self._validate(None, 25, 30)[0] is True

    def test_percentile_bounds_inclusive(self):
        assert self._validate(0, 25, 30)[0] is False
        assert self._validate(100, 25, 30)[0] is False

    def test_target_sp_must_be_below_mc_years(self):
        assert self._validate(20, 30, 30)[1] is True
        assert self._validate(20, 29, 30)[1] is False

    def test_target_sp_none_or_zero_is_invalid(self):
        assert self._validate(20, None, 30)[1] is True
        assert self._validate(20, 0, 30)[1] is True

    def test_target_sp_invalid_when_mc_years_not_int(self):
        assert self._validate(20, 25, None)[1] is True
        assert self._validate(20, 25, "abc")[1] is True

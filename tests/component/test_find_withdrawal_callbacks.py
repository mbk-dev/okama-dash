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

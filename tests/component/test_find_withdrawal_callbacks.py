"""Find max withdrawal block (issue #22): collapse + target-survival-period visibility."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import dash
import pandas as pd
import pytest

pytestmark = pytest.mark.component


def _ok_result(withdrawal_abs=-1598.95, withdrawal_rel=0.159895, error_rel=0.048, success=True):
    return SimpleNamespace(
        success=success,
        withdrawal_abs=withdrawal_abs,
        withdrawal_rel=withdrawal_rel,
        error_rel=error_rel,
    )


def _find_args(**overrides):
    """Keyword args for find_max_withdrawal with sane defaults (indexation, MC on, no backtest)."""
    kwargs = {
        "n_clicks": 1,
        "goal": "maintain_balance_pv",
        "percentile": 20,
        "target_sp": 25,
        "assets": ["SPY.US", "MSFT.US"],  # both in the AGENTS.md verified-tickers list
        "weights": [60, 40],
        "ccy": "USD",
        "rebalancing_period": "year",
        "rebal_abs_deviation": None,
        "rebal_rel_deviation": None,
        "fd_value": "2010-01",
        "ld_value": "2024-01",
        "initial_amount": 10000,
        "discount_rate": None,
        "symbol": "test",
        "cf_strategy": "indexation",
        "cf_frequency": "year",
        "cf_amount": -500,
        "cf_indexation": None,
        "cf_percentage": 0,
        "vds_percentage": 0,
        "vds_min_withdrawal": None,
        "vds_max_withdrawal": None,
        "vds_adjust_minmax": False,
        "vds_floor": None,
        "vds_ceiling": None,
        "vds_adjust_fc": False,
        "vds_indexation": None,
        "cwd_amount": 0,
        "cwd_indexation": None,
        "cwd_thresholds": [],
        "cwd_reductions": [],
        "ts_dates": [],
        "ts_amounts": [],
        "inflation_on": True,
        "n_monte_carlo": 200,
        "years_monte_carlo": 30,
        "distribution_monte_carlo": "norm",
        "show_backtest": "no",
        "mc_norm_mu": None,
        "mc_norm_sigma": None,
        "mc_lognorm_shape": None,
        "mc_lognorm_scale": None,
        "mc_t_df": None,
        "mc_t_loc": None,
        "mc_t_scale": None,
    }
    kwargs.update(overrides)
    return kwargs


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


class TestDisableFindButton:
    def _disable(self, **overrides):
        from pages.portfolio.cards_portfolio.cashflow_controls import disable_find_button

        kwargs = {
            "mc_number_valid": True,
            "mc_years_valid": True,
            "mc_number": 200,
            "initial_amount": 1000,
            "percentile_invalid": False,
            "target_sp_invalid": False,
            "goal": "maintain_balance_pv",
        }
        kwargs.update(overrides)
        return disable_find_button(**kwargs)

    def test_all_valid_enables_with_empty_hint(self):
        assert self._disable() == (False, "")

    def test_mc_number_zero_disables_with_hint(self):
        disabled, hint = self._disable(mc_number=0)
        assert disabled is True
        assert "Monte Carlo" in hint

    def test_mc_number_invalid_disables(self):
        assert self._disable(mc_number_valid=False)[0] is True

    def test_mc_years_invalid_disables(self):
        assert self._disable(mc_years_valid=False)[0] is True

    def test_empty_initial_amount_disables_with_hint(self):
        disabled, hint = self._disable(initial_amount="")
        assert disabled is True
        assert "Initial amount" in hint

    def test_none_initial_amount_disables(self):
        assert self._disable(initial_amount=None)[0] is True

    def test_invalid_percentile_disables(self):
        disabled, hint = self._disable(percentile_invalid=True)
        assert disabled is True
        assert "Percentile" in hint

    def test_invalid_target_sp_disables_only_for_survival_goal(self):
        assert self._disable(target_sp_invalid=True, goal="survival_period")[0] is True
        assert self._disable(target_sp_invalid=True, goal="maintain_balance_pv")[0] is False

    def test_positional_contract_matches_inputs_order(self):
        from pages.portfolio.cards_portfolio.cashflow_controls import disable_find_button

        # Dash passes Inputs positionally: this call mirrors the decorator's
        # Input order, guarding against a reorder that the kwargs helper hides.
        assert disable_find_button(True, True, 200, 1000, False, False, "maintain_balance_pv") == (False, "")


class TestFindMaxWithdrawalCallback:
    """Outputs: (result text, className, pf-cf-amount, pf-cf-percentage, pf-cf-vds-percentage, pf-cf-cwd-amount)."""

    def _run(self, patched_okama_portfolio, **overrides):
        from pages.portfolio.portfolio import find_max_withdrawal

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.find_the_largest_withdrawals_size = MagicMock(return_value=_ok_result())
        return mock_pf, find_max_withdrawal(**_find_args(**overrides))

    def test_indexation_fills_amount_with_negative_abs(self, patched_okama_portfolio):
        _pf, out = self._run(patched_okama_portfolio, cf_strategy="indexation")
        text, css, amount, pct, vds_pct, cwd_amount = out
        assert amount == -1598.95
        assert pct is dash.no_update
        assert vds_pct is dash.no_update
        assert cwd_amount is dash.no_update
        assert "accuracy" in text
        assert css == "ms-2"

    def test_percentage_fills_percent_with_negative_rel(self, patched_okama_portfolio):
        _pf, out = self._run(patched_okama_portfolio, cf_strategy="percentage")
        _text, _css, amount, pct, vds_pct, cwd_amount = out
        assert pct == -15.99
        assert amount is dash.no_update
        assert vds_pct is dash.no_update
        assert cwd_amount is dash.no_update

    def test_vds_fills_vds_percent(self, patched_okama_portfolio):
        _pf, out = self._run(patched_okama_portfolio, cf_strategy="vds")
        assert out[4] == -15.99
        assert out[2] is dash.no_update

    def test_cwd_fills_cwd_amount(self, patched_okama_portfolio):
        _pf, out = self._run(patched_okama_portfolio, cf_strategy="cwd")
        assert out[5] == -1598.95
        assert out[2] is dash.no_update

    def test_time_series_is_rejected_without_fills(self, patched_okama_portfolio):
        _pf, out = self._run(patched_okama_portfolio, cf_strategy="time_series")
        text, css, *fills = out
        assert "not supported" in text.lower()
        assert all(f is dash.no_update for f in fills)

    def test_solver_called_with_goal_and_percentile(self, patched_okama_portfolio):
        pf, _out = self._run(patched_okama_portfolio, goal="maintain_balance_fv", percentile=10)
        pf.dcf.find_the_largest_withdrawals_size.assert_called_once_with(
            goal="maintain_balance_fv", percentile=10
        )

    def test_survival_goal_passes_target_survival_period(self, patched_okama_portfolio):
        pf, _out = self._run(patched_okama_portfolio, goal="survival_period", target_sp=20)
        pf.dcf.find_the_largest_withdrawals_size.assert_called_once_with(
            goal="survival_period", percentile=20, target_survival_period=20
        )

    def test_set_mc_parameters_mirrors_submit_inputs(self, patched_okama_portfolio):
        pf, _out = self._run(patched_okama_portfolio)
        pf.dcf.set_mc_parameters.assert_called_once_with(
            distribution="norm",
            distribution_parameters=None,
            period=30,
            mc_number=200,
        )

    def test_no_backtest_keeps_initial_investment(self, patched_okama_portfolio):
        pf, _out = self._run(patched_okama_portfolio, show_backtest="no")
        # The no-backtest branch must not compute the backtest wealth index
        # (1000 -> 1000 alone would not discriminate the branch taken);
        # initial_investment is re-applied unchanged (mock default 1000).
        pf.dcf.wealth_index.assert_not_called()
        assert pf.dcf.cashflow_parameters.initial_investment == 1000

    def test_backtest_overrides_initial_investment_with_last_value(self, patched_okama_portfolio):
        pf = patched_okama_portfolio["portfolio_instance"]
        pf.dcf.wealth_index = MagicMock(
            return_value=pd.DataFrame({pf.symbol: [1000.0, 1500.0]})
        )
        _pf, _out = self._run(patched_okama_portfolio, show_backtest="yes")
        assert pf.dcf.cashflow_parameters.initial_investment == 1500.0

    def test_depleted_backtest_renders_message_without_fills(self, patched_okama_portfolio):
        pf = patched_okama_portfolio["portfolio_instance"]
        pf.dcf.wealth_index = MagicMock(
            return_value=pd.DataFrame({pf.symbol: [1000.0, 0.0]})
        )
        _pf, out = self._run(patched_okama_portfolio, show_backtest="yes")
        text, css, *fills = out
        assert "depleted" in text.lower()
        assert css == "ms-2 text-warning"
        assert all(f is dash.no_update for f in fills)

    def test_no_solution_renders_warning_without_fills(self, patched_okama_portfolio):
        pf = patched_okama_portfolio["portfolio_instance"]
        pf.dcf.find_the_largest_withdrawals_size = MagicMock(return_value=_ok_result(success=False))
        from pages.portfolio.portfolio import find_max_withdrawal

        text, css, *fills = find_max_withdrawal(**_find_args())
        assert "No solution found" in text
        assert css == "ms-2 text-warning"
        assert all(f is dash.no_update for f in fills)

    def test_value_error_renders_danger_message(self, patched_okama_portfolio):
        pf = patched_okama_portfolio["portfolio_instance"]
        pf.dcf.find_the_largest_withdrawals_size = MagicMock(
            side_effect=ValueError("withdrawal size must be negative")
        )
        from pages.portfolio.portfolio import find_max_withdrawal

        text, css, *fills = find_max_withdrawal(**_find_args())
        assert "withdrawal size must be negative" in text
        assert css == "ms-2 text-danger"
        assert all(f is dash.no_update for f in fills)

    def test_unexpected_error_renders_generic_danger_message(self, patched_okama_portfolio):
        pf = patched_okama_portfolio["portfolio_instance"]
        pf.dcf.find_the_largest_withdrawals_size = MagicMock(side_effect=RuntimeError("boom"))
        from pages.portfolio.portfolio import find_max_withdrawal

        text, css, *fills = find_max_withdrawal(**_find_args())
        assert "boom" not in text  # generic message, no internals leaked
        assert css == "ms-2 text-danger"
        assert all(f is dash.no_update for f in fills)

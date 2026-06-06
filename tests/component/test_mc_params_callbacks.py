from unittest.mock import MagicMock, patch

import dash
import pandas as pd
import pytest

from tests.mocks.okama_mock import make_mock_portfolio

pytestmark = pytest.mark.component

PF_MODULE = "pages.portfolio.portfolio"


def _outer_default_args():
    return {
        "screen": None,
        "log_on": False,
        "assets": ["AAPL.US", "MSFT.US"],
        "weights": [50, 50],
        "ccy": "USD",
        "rebalancing_period": "month",
        "rebal_abs_deviation": None,
        "rebal_rel_deviation": None,
        "fd_value": "2020-01",
        "ld_value": "2024-12",
        "initial_amount": 1000,
        "discount_rate": 0,
        "symbol": "TestPF",
        "cf_strategy": "indexation",
        "cf_frequency": "month",
        "cf_amount": 0,
        "cf_indexation": 0,
        "cf_percentage": 0,
        "vds_percentage": 0,
        "vds_min_withdrawal": 0,
        "vds_max_withdrawal": 0,
        "vds_adjust_minmax": True,
        "vds_floor": 0,
        "vds_ceiling": 0,
        "vds_adjust_fc": False,
        "vds_indexation": 0,
        "cwd_amount": 0,
        "cwd_indexation": 0,
        "cwd_thresholds": [],
        "cwd_reductions": [],
        "ts_dates": [],
        "ts_amounts": [],
        "plot_type": "wealth",
        "inflation_on": False,
        "rolling_window": 2,
        "n_monte_carlo": 100,
        "years_monte_carlo": 10,
        "distribution_monte_carlo": "t",
        "show_backtest": "no",
    }


class TestDistributionParametersWiring:
    def test_get_pf_figure_passes_distribution_parameters_to_set_mc(self):
        from pages.portfolio.portfolio import get_pf_figure

        pf = make_mock_portfolio()
        pf.dcf.set_mc_parameters = MagicMock()
        # monte_carlo_wealth needs to return a DataFrame with a period index
        mc_df = pd.DataFrame(
            {"portfolio": [1000.0, 1050.0, 1100.0]},
            index=pd.period_range("2020-01", periods=3, freq="M"),
        )
        pf.dcf.monte_carlo_wealth = MagicMock(return_value=mc_df)

        get_pf_figure(
            pf,
            plot_type="wealth",
            inflation_on=False,
            rolling_window=2,
            n_monte_carlo=100,
            years_monte_carlo=10,
            distribution_monte_carlo="t",
            show_backtest="no",
            log_scale=False,
            cf_strategy="indexation",
            distribution_parameters_monte_carlo=(3.4, 0.006, 0.038),
        )

        pf.dcf.set_mc_parameters.assert_called_once_with(
            distribution="t",
            distribution_parameters=(3.4, 0.006, 0.038),
            period=10,
            mc_number=100,
        )


class TestSubmitBuildsParameters:
    def test_submit_passes_t_parameters_to_inner(self):
        from pages.portfolio.portfolio import update_graf_portfolio

        with (
            patch(f"{PF_MODULE}.dash.ctx") as mock_ctx,
            patch(f"{PF_MODULE}._update_graf_portfolio_inner", return_value=(None,) * 6) as mock_inner,
        ):
            mock_ctx.triggered_id = "pf-submit-button"
            update_graf_portfolio(
                **_outer_default_args(),
                n_clicks=1,
                mc_norm_mu=None,
                mc_norm_sigma=None,
                mc_lognorm_shape=None,
                mc_lognorm_scale=None,
                mc_t_df=3.4,
                mc_t_loc=0.006,
                mc_t_scale=0.038,
            )

        passed = mock_inner.call_args.kwargs["distribution_parameters_monte_carlo"]
        assert passed == (3.4, 0.006, 0.038)


class TestShowHideParamGroups:
    def test_norm_shows_only_norm(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import show_hide_param_groups

        norm, lognorm, t = show_hide_param_groups("norm")
        assert norm is None
        assert lognorm == {"display": "none"}
        assert t == {"display": "none"}

    def test_lognorm_shows_only_lognorm(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import show_hide_param_groups

        norm, lognorm, t = show_hide_param_groups("lognorm")
        assert lognorm is None
        assert norm == {"display": "none"}
        assert t == {"display": "none"}

    def test_t_shows_only_t(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import show_hide_param_groups

        norm, lognorm, t = show_hide_param_groups("t")
        assert t is None
        assert norm == {"display": "none"}
        assert lognorm == {"display": "none"}


class TestToggleMcParamsCollapse:
    def test_opens_from_closed(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import toggle_mc_params_collapse

        is_open, chevron = toggle_mc_params_collapse(1, False)
        assert is_open is True
        assert "chevron-down" in chevron

    def test_closes_from_open(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import toggle_mc_params_collapse

        is_open, chevron = toggle_mc_params_collapse(2, True)
        assert is_open is False
        assert "chevron-right" in chevron


class TestHideMonteCarloRows:
    def test_non_wealth_hides_all_six(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import hide_monte_carlo_rows

        result = hide_monte_carlo_rows("drawdowns", 100)
        assert len(result) == 6
        assert all(style == {"display": "none"} for style in result)

    def test_cumulative_return_hides_all_six(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import hide_monte_carlo_rows

        result = hide_monte_carlo_rows("cumulative_return", 100)
        assert len(result) == 6
        assert all(style == {"display": "none"} for style in result)

    def test_wealth_zero_mc_hides_params_row(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import hide_monte_carlo_rows

        header, number, period, distribution, params, backtest = hide_monte_carlo_rows("wealth", 0)
        assert header is None
        assert number is None
        assert params == {"display": "none"}

    def test_wealth_with_mc_shows_params_row(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import hide_monte_carlo_rows

        result = hide_monte_carlo_rows("wealth", 100)
        assert len(result) == 6
        assert all(style is None for style in result)


class TestCallbackRegistration:
    def test_mc_params_outputs_bound_to_auto_estimate(self):
        """The @callback decorator must be attached to auto_estimate_distribution_parameters.

        Regression guard: a refactor once inserted helper defs between the decorator
        and the function, silently registering the helper as the Dash callback
        (TypeError 500 in the browser while direct-call tests stayed green).
        """
        from dash._callback import GLOBAL_CALLBACK_MAP

        import pages.portfolio.portfolio  # noqa: F401  # ensures callbacks are registered

        key = next(k for k in GLOBAL_CALLBACK_MAP if "pf-mc-norm-mu.value" in k)
        bound = GLOBAL_CALLBACK_MAP[key]["callback"]
        assert bound.__name__ == "auto_estimate_distribution_parameters"


class TestAutoEstimateDistributionParameters:
    def _form_state(self, **overrides):
        state = {
            "assets": ["AAPL.US", "MSFT.US"],
            "weights": [50, 50],
            "ccy": "USD",
            "fd": "2020-01",
            "ld": "2024-12",
            "rebal": "month",
            "abs_dev": None,
            "rel_dev": None,
            "distribution": "norm",
            "var_level": None,
        }
        state.update(overrides)
        return state

    def _call(self, trigger, **overrides):
        from pages.portfolio.portfolio import auto_estimate_distribution_parameters

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = trigger
            return auto_estimate_distribution_parameters(**self._form_state(**overrides))

    def test_incomplete_weights_no_recompute(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        result = self._call("pf-base-currency", weights=[50, 40])

        assert all(r is dash.no_update for r in result)
        mock_pf.dcf.mc.get_parameters_for_distribution.assert_not_called()

    def test_missing_ticker_no_recompute(self, patched_okama_portfolio):
        result = self._call("pf-base-currency", assets=[None, "MSFT.US"])

        assert all(r is dash.no_update for r in result)

    def test_partial_date_no_recompute(self, patched_okama_portfolio):
        result = self._call("pf-first-date", fd="202")

        assert all(r is dash.no_update for r in result)

    def test_fit_fills_norm_group_without_status_message(self, patched_okama_portfolio):
        """Successful estimation must leave the status line empty (no debug timing text)."""
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (0.007, 0.04)

        result = self._call("pf-base-currency", distribution="norm")

        assert len(result) == 8
        assert result[0] == 0.007
        assert result[1] == 0.04
        assert result[4] is dash.no_update
        assert result[7] == ""

    def test_fit_fills_lognorm_group(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (0.05, -1.0, 1.01)

        result = self._call("pf-base-currency", distribution="lognorm")

        assert len(result) == 8
        assert result[2] == 0.05
        assert result[3] == 1.01
        assert result[0] is dash.no_update

    def test_portfolio_trigger_fills_fitted_df_for_t(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (3.4, 0.006, 0.038)

        result = self._call("pf-base-currency", distribution="t", var_level=5)

        assert len(result) == 8
        assert result[4] == 3.4
        assert result[5] == 0.006
        assert result[6] == 0.038
        mock_pf.dcf.mc.optimize_df_for_students.assert_not_called()

    def test_var_level_change_optimizes_df(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.optimize_df_for_students.return_value = 7.5

        result = self._call("pf-mc-t-var-level", distribution="t", var_level=5)

        assert len(result) == 8
        assert result[4] == 7.5
        assert result[0] is dash.no_update
        assert result[5] is dash.no_update
        assert result[7] == ""
        mock_pf.dcf.mc.optimize_df_for_students.assert_called_once_with(5)
        mock_pf.dcf.mc.get_parameters_for_distribution.assert_not_called()

    def test_var_level_ignored_for_non_t(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        result = self._call("pf-mc-t-var-level", distribution="norm", var_level=5)

        assert all(r is dash.no_update for r in result)
        mock_pf.dcf.mc.optimize_df_for_students.assert_not_called()

    def test_clearing_var_level_resets_df_to_fitted(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (3.4, 0.006, 0.038)

        result = self._call("pf-mc-t-var-level", distribution="t", var_level=None)

        assert len(result) == 8
        assert result[4] == 3.4  # df back to the fitted value
        assert result[5] is dash.no_update  # loc untouched
        assert result[6] is dash.no_update  # scale untouched
        assert result[7] == ""
        mock_pf.dcf.mc.optimize_df_for_students.assert_not_called()

    def test_estimate_failure_returns_message(self, patched_okama_portfolio):
        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.side_effect = ValueError("no data")

        result = self._call("pf-base-currency", distribution="norm")

        assert len(result) == 8
        assert result[0] is dash.no_update
        assert "no data" in str(result[7])


class TestValidateDf:
    def test_df_below_threshold_is_invalid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_df

        assert validate_df(2) is True
        assert validate_df(1.5) is True

    def test_df_above_threshold_is_valid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_df

        assert validate_df(3) is False

    def test_empty_df_is_not_invalid(self):
        from pages.portfolio.cards_portfolio.portfolio_controls import validate_df

        assert validate_df(None) is False
        assert validate_df("") is False

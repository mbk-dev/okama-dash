from unittest.mock import MagicMock, patch

import dash
import pandas as pd
import pytest

from tests.mocks.okama_mock import make_mock_portfolio

pytestmark = pytest.mark.component

PF_MODULE = "pages.portfolio.portfolio"


def _outer_default_args():
    return {
        "screen": None, "log_on": False,
        "assets": ["AAPL.US", "MSFT.US"], "weights": [50, 50],
        "ccy": "USD", "rebalancing_period": "month",
        "rebal_abs_deviation": None, "rebal_rel_deviation": None,
        "fd_value": "2020-01", "ld_value": "2024-12",
        "initial_amount": 1000, "discount_rate": 0, "symbol": "TestPF",
        "cf_strategy": "indexation", "cf_frequency": "month",
        "cf_amount": 0, "cf_indexation": 0, "cf_percentage": 0,
        "vds_percentage": 0, "vds_min_withdrawal": 0, "vds_max_withdrawal": 0,
        "vds_adjust_minmax": True, "vds_floor": 0, "vds_ceiling": 0,
        "vds_adjust_fc": False, "vds_indexation": 0,
        "cwd_amount": 0, "cwd_indexation": 0, "cwd_thresholds": [], "cwd_reductions": [],
        "ts_dates": [], "ts_amounts": [],
        "plot_type": "wealth", "inflation_on": False, "rolling_window": 2,
        "n_monte_carlo": 100, "years_monte_carlo": 10,
        "distribution_monte_carlo": "t", "show_backtest": "no",
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
            pf, plot_type="wealth", inflation_on=False, rolling_window=2,
            n_monte_carlo=100, years_monte_carlo=10, distribution_monte_carlo="t",
            show_backtest="no", log_scale=False, cf_strategy="indexation",
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
                **_outer_default_args(), n_clicks=1,
                mc_norm_mu=None, mc_norm_sigma=None,
                mc_lognorm_shape=None, mc_lognorm_scale=None,
                mc_t_df=3.4, mc_t_loc=0.006, mc_t_scale=0.038,
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


class TestFillDistributionParameters:
    def _portfolio_states(self):
        return {
            "assets": ["AAPL.US", "MSFT.US"], "weights": [50, 50], "ccy": "USD",
            "fd": "2020-01", "ld": "2024-12", "rebal": "month",
            "abs_dev": None, "rel_dev": None,
        }

    def test_estimate_fills_t_group(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import fill_distribution_parameters

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (3.4, 0.006, 0.038)

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-mc-estimate-btn"
            result = fill_distribution_parameters(
                1, 0, 5, **self._portfolio_states(), distribution="t",
            )

        # outputs order: mu, sigma, shape, scale_ln, df, loc_t, scale_t, message
        assert result[4] == 3.4
        assert result[5] == 0.006
        assert result[6] == 0.038
        assert result[0] is dash.no_update

    def test_estimate_fills_norm_group(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import fill_distribution_parameters

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.return_value = (0.007, 0.04)

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-mc-estimate-btn"
            result = fill_distribution_parameters(
                1, 0, 5, **self._portfolio_states(), distribution="norm",
            )

        assert result[0] == 0.007
        assert result[1] == 0.04
        assert result[4] is dash.no_update

    def test_optimize_writes_df(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import fill_distribution_parameters

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.optimize_df_for_students.return_value = 7.5

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-mc-t-optimize-btn"
            result = fill_distribution_parameters(
                0, 1, 5, **self._portfolio_states(), distribution="t",
            )

        assert result[4] == 7.5
        assert result[0] is dash.no_update
        mock_pf.dcf.mc.optimize_df_for_students.assert_called_once_with(5)

    def test_estimate_failure_returns_message(self, patched_okama_portfolio):
        from pages.portfolio.portfolio import fill_distribution_parameters

        mock_pf = patched_okama_portfolio["portfolio_instance"]
        mock_pf.dcf.mc.get_parameters_for_distribution.side_effect = ValueError("no data")

        with patch(f"{PF_MODULE}.dash.ctx") as mock_ctx:
            mock_ctx.triggered_id = "pf-mc-estimate-btn"
            result = fill_distribution_parameters(
                1, 0, 5, **self._portfolio_states(), distribution="norm",
            )

        assert result[0] is dash.no_update
        assert "no data" in str(result[7])

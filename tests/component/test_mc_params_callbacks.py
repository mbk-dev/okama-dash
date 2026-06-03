from unittest.mock import MagicMock

import pandas as pd
import pytest

from tests.mocks.okama_mock import make_mock_portfolio

pytestmark = pytest.mark.component


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

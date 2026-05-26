import json
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_symbols_data() -> dict:
    with open(FIXTURES_DIR / "symbols_data.json") as f:
        return json.load(f)


def mock_symbols_in_namespace(namespace: str) -> pd.DataFrame:
    data = load_symbols_data()
    ns_data = data["symbols_by_namespace"].get(namespace, {"symbol": [], "name": []})
    return pd.DataFrame(ns_data)


def get_mock_namespaces() -> list[str]:
    return load_symbols_data()["namespaces"]


def make_mock_portfolio() -> MagicMock:
    mock = MagicMock()
    mock.symbol = "TestPF.PF"
    mock.symbols = ["AAPL.US", "MSFT.US"]
    mock.currency = "USD"
    mock.weights = [0.5, 0.5]
    mock.first_date = pd.Timestamp("2020-01-01")
    mock.last_date = pd.Timestamp("2024-12-01")

    rebal_strategy = MagicMock()
    rebal_strategy.period = "month"
    mock.rebalancing_strategy = rebal_strategy

    dates = pd.period_range("2020-01", "2024-12", freq="M")
    n = len(dates)
    rng = np.random.default_rng(42)

    wealth_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, 3)), axis=0) * 1000
    mock.wealth_index_with_assets = pd.DataFrame(
        wealth_data,
        index=dates,
        columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
    )

    mock.ror = pd.Series(rng.normal(0.005, 0.03, n), index=dates)

    describe_data = {
        "property": ["CAGR", "Risk", "CVAR"],
        "period": ["annually", "annually", "annually"],
        "TestPF.PF": [0.08, 0.12, -0.15],
    }
    mock.describe.return_value = pd.DataFrame(describe_data)
    mock._pl_txt = "annually"

    mock.skewness = pd.DataFrame({"TestPF.PF": [-0.1]})
    mock.kurtosis = pd.DataFrame({"TestPF.PF": [3.2]})
    mock.jarque_bera = {"statistic": 2.5, "p-value": 0.29}
    mock.kstest.return_value = {"statistic": 0.05, "p-value": 0.80}

    mock.drawdowns = pd.Series(rng.uniform(-0.2, 0, n), index=dates, name="TestPF.PF")

    cumulative_return = pd.Series(
        [0.08, 0.10, 0.07],
        index=["TestPF.PF", "AAPL.US", "MSFT.US"],
    )
    mock.get_cumulative_return.return_value = cumulative_return
    mock.get_rolling_cagr.return_value = pd.DataFrame(
        rng.normal(0.08, 0.02, (n, 3)),
        index=dates,
        columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
    )
    mock.get_sharpe_ratio.return_value = 0.65

    inflation_ts = pd.Series(rng.normal(0.002, 0.001, n), index=dates)
    mock.inflation_ts = inflation_ts

    dcf = MagicMock()
    dcf.use_discounted_values = True
    dcf.discount_rate = 0.05

    cf_params = MagicMock()
    cf_params.amount = 0
    cf_params.initial_investment = 1000
    dcf.cashflow_parameters = cf_params

    dcf.wealth_index_fv_with_assets = mock.wealth_index_with_assets.copy()
    dcf.monte_carlo_wealth = pd.DataFrame()
    dcf.survival_period_hist.return_value = 25.0
    mock.dcf = dcf

    return mock

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


def make_mock_asset_list(symbols: list[str] | None = None) -> MagicMock:
    if symbols is None:
        symbols = ["AAPL.US", "MSFT.US"]
    mock = MagicMock()
    mock.symbols = symbols
    mock.symbol = symbols[0] if len(symbols) == 1 else "AssetList"
    mock._pl_txt = "annually"

    dates = pd.period_range("2020-01", "2024-12", freq="M")
    n = len(dates)
    n_assets = len(symbols)
    rng = np.random.default_rng(42)

    wealth_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, n_assets)), axis=0) * 1000
    mock.wealth_indexes = pd.DataFrame(wealth_data, index=dates, columns=symbols)

    ror_data = rng.normal(0.005, 0.03, (n, n_assets))
    mock.assets_ror = pd.DataFrame(ror_data, index=dates, columns=symbols)

    mock.get_cumulative_return = MagicMock(
        return_value=pd.Series(rng.uniform(0.05, 0.20, n_assets), index=symbols)
    )
    mock.get_rolling_cagr = MagicMock(
        return_value=pd.DataFrame(rng.normal(0.08, 0.02, (n, n_assets)), index=dates, columns=symbols)
    )
    mock.get_sharpe_ratio = MagicMock(
        return_value=pd.Series(rng.uniform(0.3, 1.0, n_assets), index=symbols)
    )

    describe_data = {
        "property": [
            "CAGR", "Risk", "CVAR", "Max drawdown",
            "Max dd date start", "Max dd date end", "Max dd days", "Dividend yield",
        ],
        "period": ["annually"] * 8,
    }
    for s in symbols:
        describe_data[s] = rng.uniform(-0.05, 0.20, 8).tolist()
    mock.describe = MagicMock(return_value=pd.DataFrame(describe_data))

    mock.inflation_ts = pd.Series(dtype=float)

    # Benchmark-specific methods
    ts_data = rng.normal(0.0, 0.02, (n, max(n_assets - 1, 1)))
    ts_cols = symbols[1:] if n_assets > 1 else symbols
    mock.tracking_difference = MagicMock(
        return_value=pd.DataFrame(ts_data, index=dates, columns=ts_cols)
    )
    mock.tracking_difference_annualized = MagicMock(
        return_value=pd.DataFrame(ts_data, index=dates, columns=ts_cols)
    )

    annual_dates = pd.period_range("2020", "2024", freq="Y")
    annual_data = rng.normal(0.0, 0.03, (len(annual_dates), max(n_assets - 1, 1)))
    mock.tracking_difference_annual = pd.DataFrame(annual_data, index=annual_dates, columns=ts_cols)

    mock.tracking_error = MagicMock(
        return_value=pd.DataFrame(np.abs(ts_data), index=dates, columns=ts_cols)
    )
    mock.index_corr = MagicMock(
        return_value=pd.DataFrame(rng.uniform(0.8, 1.0, (n, max(n_assets - 1, 1))), index=dates, columns=ts_cols)
    )
    mock.index_beta = MagicMock(
        return_value=pd.DataFrame(rng.uniform(0.8, 1.2, (n, max(n_assets - 1, 1))), index=dates, columns=ts_cols)
    )

    return mock


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

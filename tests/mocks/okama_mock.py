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


# ---------------------------------------------------------------------------
# Picklable mock classes (for E2E tests that go through pickle.dump)
# ---------------------------------------------------------------------------

class _RebalanceStrategy:
    def __init__(self, period: str = "month"):
        self.period = period


class _CashflowParameters:
    def __init__(self, amount: float = 0, initial_investment: float = 1000):
        self.amount = amount
        self.initial_investment = initial_investment


class _DCF:
    def __init__(self, wealth_index_df: pd.DataFrame):
        self.use_discounted_values = True
        self.discount_rate = 0.05
        self.cashflow_parameters = _CashflowParameters()
        self._wealth_index_df = wealth_index_df
        self._mc_params: dict = {}

    def wealth_index(self, discounting: str = "fv", include_negative_values: bool = True) -> pd.DataFrame:
        return self._wealth_index_df.copy()

    def set_mc_parameters(self, distribution: str = "norm", period: int = 0, mc_number: int = 0):
        self._mc_params = {"distribution": distribution, "period": period, "mc_number": mc_number}

    def monte_carlo_wealth(self, discounting: str = "fv") -> pd.DataFrame:
        return pd.DataFrame()

    def survival_period_hist(self) -> float:
        return 25.0

    def monte_carlo_survival_period(self, threshold: float = 0) -> pd.Series:
        return pd.Series([25.0, 30.0, 20.0])


class PicklablePortfolio:
    def __init__(self):
        self.symbol = "TestPF.PF"
        self.symbols = ["AAPL.US", "MSFT.US"]
        self.currency = "USD"
        self.weights = [0.5, 0.5]
        self.first_date = pd.Timestamp("2020-01-01")
        self.last_date = pd.Timestamp("2024-12-01")
        self.rebalancing_strategy = _RebalanceStrategy()
        self._pl_txt = "annually"

        dates = pd.period_range("2020-01", "2024-12", freq="M")
        n = len(dates)
        rng = np.random.default_rng(42)

        wealth_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, 3)), axis=0) * 1000
        self.wealth_index_with_assets = pd.DataFrame(
            wealth_data, index=dates, columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
        )
        self.ror = pd.Series(rng.normal(0.005, 0.03, n), index=dates)
        self.drawdowns = pd.Series(rng.uniform(-0.2, 0, n), index=dates, name="TestPF.PF")
        self.inflation_ts = pd.Series(rng.normal(0.002, 0.001, n), index=dates)
        self.skewness = pd.DataFrame({"TestPF.PF": [-0.1]})
        self.kurtosis = pd.DataFrame({"TestPF.PF": [3.2]})
        self.jarque_bera = {"statistic": 2.5, "p-value": 0.29}

        self.dcf = _DCF(self.wealth_index_with_assets.copy())

        self._dates = dates
        self._n = n
        self._rng = rng

    def describe(self) -> pd.DataFrame:
        return pd.DataFrame({
            "property": ["CAGR", "Risk", "CVAR"],
            "period": ["annually", "annually", "annually"],
            "TestPF.PF": [0.08, 0.12, -0.15],
        })

    def get_cumulative_return(self, real: bool = False) -> pd.Series:
        return pd.Series([0.08, 0.10, 0.07], index=["TestPF.PF", "AAPL.US", "MSFT.US"])

    def get_rolling_cagr(self, window: int | None = None, real: bool = False) -> pd.DataFrame:
        return pd.DataFrame(
            self._rng.normal(0.08, 0.02, (self._n, 3)),
            index=self._dates, columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
        )

    def get_sharpe_ratio(self, rf_return: float = 0.0) -> float:
        return 0.65

    def kstest(self, distribution: str = "norm") -> dict:
        return {"statistic": 0.05, "p-value": 0.80}


class PicklableAssetList:
    def __init__(self, symbols: list[str] | None = None, **kwargs):
        if symbols is None:
            symbols = ["AAPL.US", "MSFT.US"]
        self.symbols = symbols
        self.symbol = symbols[0] if len(symbols) == 1 else "AssetList"
        self._pl_txt = "annually"

        dates = pd.period_range("2020-01", "2024-12", freq="M")
        n = len(dates)
        n_assets = len(symbols)
        rng = np.random.default_rng(42)

        wealth_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, n_assets)), axis=0) * 1000
        self.wealth_indexes = pd.DataFrame(wealth_data, index=dates, columns=symbols)

        ror_data = rng.normal(0.005, 0.03, (n, n_assets))
        self.assets_ror = pd.DataFrame(ror_data, index=dates, columns=symbols)
        self.inflation_ts = pd.Series(dtype=float)

        ts_cols = symbols[1:] if n_assets > 1 else symbols
        ts_data = rng.normal(0.0, 0.02, (n, max(n_assets - 1, 1)))
        self._ts_data = pd.DataFrame(ts_data, index=dates, columns=ts_cols)
        self._ts_abs = pd.DataFrame(np.abs(ts_data), index=dates, columns=ts_cols)

        annual_dates = pd.period_range("2020", "2024", freq="Y")
        annual_data = rng.normal(0.0, 0.03, (len(annual_dates), max(n_assets - 1, 1)))
        self.tracking_difference_annual = pd.DataFrame(annual_data, index=annual_dates, columns=ts_cols)

        self._corr_data = pd.DataFrame(
            rng.uniform(0.8, 1.0, (n, max(n_assets - 1, 1))), index=dates, columns=ts_cols,
        )
        self._beta_data = pd.DataFrame(
            rng.uniform(0.8, 1.2, (n, max(n_assets - 1, 1))), index=dates, columns=ts_cols,
        )
        self._cum_return = pd.Series(rng.uniform(0.05, 0.20, n_assets), index=symbols)
        self._rolling_cagr = pd.DataFrame(
            rng.normal(0.08, 0.02, (n, n_assets)), index=dates, columns=symbols,
        )
        self._sharpe = pd.Series(rng.uniform(0.3, 1.0, n_assets), index=symbols)
        self._describe = self._build_describe(symbols, rng)

    @staticmethod
    def _build_describe(symbols, rng):
        data = {
            "property": [
                "CAGR", "Risk", "CVAR", "Max drawdown",
                "Max dd date start", "Max dd date end", "Max dd days", "Dividend yield",
            ],
            "period": ["annually"] * 8,
        }
        for s in symbols:
            data[s] = rng.uniform(-0.05, 0.20, 8).tolist()
        return pd.DataFrame(data)

    def get_cumulative_return(self, real: bool = False) -> pd.Series:
        return self._cum_return

    def get_rolling_cagr(self, window: int | None = None, real: bool = False) -> pd.DataFrame:
        return self._rolling_cagr

    def get_sharpe_ratio(self, rf_return: float = 0.0) -> pd.Series:
        return self._sharpe

    def describe(self) -> pd.DataFrame:
        return self._describe.copy()

    def tracking_difference(self, rolling_window: int | None = None) -> pd.DataFrame:
        return self._ts_data

    def tracking_difference_annualized(self, rolling_window: int | None = None) -> pd.DataFrame:
        return self._ts_data

    def tracking_error(self, rolling_window: int | None = None) -> pd.DataFrame:
        return self._ts_abs

    def index_corr(self, rolling_window: int | None = None) -> pd.DataFrame:
        return self._corr_data

    def index_beta(self, rolling_window: int | None = None) -> pd.DataFrame:
        return self._beta_data


# ---------------------------------------------------------------------------
# MagicMock-based factories (used by component tests that don't pickle)
# ---------------------------------------------------------------------------

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

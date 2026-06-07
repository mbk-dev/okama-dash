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


def get_names_by_symbol() -> dict[str, str]:
    """Symbol -> display name mapping across all fixture namespaces."""
    namespaces = load_symbols_data()["symbols_by_namespace"]
    return {
        symbol: name
        for ns_data in namespaces.values()
        for symbol, name in zip(ns_data["symbol"], ns_data["name"], strict=True)
    }


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


class _MC:
    """Picklable mock for okama MonteCarlo object."""

    def __init__(self):
        self.distribution = "norm"
        self.distribution_parameters = None

    def get_parameters_for_distribution(self) -> tuple:
        """Return fixed distribution parameters per self.distribution."""
        params_map = {
            "norm": (0.007, 0.04),
            "lognorm": (0.05, -1.0, 1.01),
            "t": (3.4, 0.006, 0.038),
        }
        return params_map.get(self.distribution, (0.0, 1.0))

    def optimize_df_for_students(self, var_level: float) -> float:
        """Return a fixed degrees-of-freedom value."""
        return 7.5


class _DCF:
    def __init__(self, wealth_index_df: pd.DataFrame):
        self.use_discounted_values = True
        self.discount_rate = 0.05
        self.cashflow_parameters = _CashflowParameters()
        self._wealth_index_df = wealth_index_df
        self._mc_params: dict = {}
        self.mc = _MC()

    def wealth_index(self, discounting: str = "fv", include_negative_values: bool = True) -> pd.DataFrame:
        return self._wealth_index_df.copy()

    def set_mc_parameters(
        self, distribution: str = "norm", distribution_parameters=None, period: int = 0, mc_number: int = 0
    ):
        self._mc_params = {
            "distribution": distribution,
            "distribution_parameters": distribution_parameters,
            "period": period,
            "mc_number": mc_number,
        }

    def monte_carlo_wealth(self, discounting: str = "fv", include_negative_values: bool = True) -> pd.DataFrame:
        return pd.DataFrame()

    def survival_period_hist(self) -> float:
        return 25.0

    def monte_carlo_survival_period(self, threshold: float = 0) -> pd.Series:
        return pd.Series([25.0, 30.0, 20.0])

    def monte_carlo_irr(self) -> pd.Series:
        return pd.Series([0.04, 0.05, 0.06])

    def irr(self) -> float:
        return 0.045


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
            wealth_data,
            index=dates,
            columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
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
        return pd.DataFrame(
            {
                "property": ["CAGR", "Risk", "CVAR"],
                "period": ["annually", "annually", "annually"],
                "TestPF.PF": [0.08, 0.12, -0.15],
            }
        )

    def get_cumulative_return(self, real: bool = False) -> pd.DataFrame:
        # Mirrors okama 2.1.1: Portfolio.get_cumulative_return returns an expanding
        # time series with the portfolio column only (plus inflation if enabled).
        cum_data = np.cumprod(1 + self.ror.to_numpy()[:, None], axis=0) - 1.0
        return pd.DataFrame(cum_data, index=self._dates, columns=["TestPF.PF"])

    def get_rolling_cagr(self, window: int | None = None, real: bool = False) -> pd.DataFrame:
        return pd.DataFrame(
            self._rng.normal(0.08, 0.02, (self._n, 3)),
            index=self._dates,
            columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
        )

    def get_sharpe_ratio(self, rf_return: float = 0.0) -> float:
        return 0.65

    def kstest(self, distribution: str = "norm") -> dict:
        return {"statistic": 0.05, "p-value": 0.80}

    def annual_return_ts(self, return_type: str = "cagr") -> pd.Series:
        # Portfolio.annual_return_ts is a method returning a Series (one value per year)
        annual_idx = pd.period_range("2020", "2024", freq="Y")
        rng = np.random.default_rng(7)
        return pd.Series(rng.normal(0.05, 0.1, len(annual_idx)), index=annual_idx, name=self.symbol)


class PicklableAssetList:
    def __init__(self, symbols: list[str] | None = None, **kwargs):
        if symbols is None:
            symbols = ["AAPL.US", "MSFT.US"]
        self.symbols = symbols
        self.symbol = symbols[0] if len(symbols) == 1 else "AssetList"
        self._pl_txt = "annually"
        self.currency = kwargs.get("ccy", "USD")
        # Real AssetList.names maps each symbol to its long name (issue #13);
        # unknown symbols fall back to the ticker itself.
        names_by_symbol = get_names_by_symbol()
        self.names = {s: names_by_symbol.get(s, s) for s in symbols}

        dates = pd.period_range("2020-01", "2024-12", freq="M")
        n = len(dates)
        n_assets = len(symbols)
        rng = np.random.default_rng(42)

        # Attributes read by common/html_elements/info_ag_grid.py::get_info.
        # Real assets_first_dates lists assets eldest-first and includes the
        # currency entry, which get_info pops before reading the eldest ticker.
        self.first_date = dates[0].to_timestamp()
        self.last_date = dates[-1].to_timestamp()
        self.assets_first_dates = dict.fromkeys(symbols, self.first_date)
        self.assets_first_dates[self.currency] = self.first_date
        self.newest_asset = symbols[-1]

        wealth_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, n_assets)), axis=0) * 1000
        self.wealth_indexes = pd.DataFrame(wealth_data, index=dates, columns=symbols)

        # Real AssetList appends the list-currency inflation column when
        # inflation=True (verified live: columns = symbols + f"{ccy}.INFL").
        if kwargs.get("inflation"):
            infl_col = f"{self.currency}.INFL"
            self.wealth_indexes[infl_col] = np.cumprod(1 + rng.normal(0.003, 0.002, n)) * 1000

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

        # AssetList.annual_return_ts is a property returning a DataFrame (one column per asset)
        self.annual_return_ts = pd.DataFrame(
            rng.normal(0.05, 0.1, (len(annual_dates), n_assets)),
            index=annual_dates,
            columns=symbols,
        )

        self._corr_data = pd.DataFrame(
            rng.uniform(0.8, 1.0, (n, max(n_assets - 1, 1))),
            index=dates,
            columns=ts_cols,
        )
        self._beta_data = pd.DataFrame(
            rng.uniform(0.8, 1.2, (n, max(n_assets - 1, 1))),
            index=dates,
            columns=ts_cols,
        )
        cum_return_data = np.cumprod(1 + ror_data, axis=0) - 1.0
        self._cum_return = pd.DataFrame(cum_return_data, index=dates, columns=symbols)
        self._rolling_cagr = pd.DataFrame(
            rng.normal(0.08, 0.02, (n, n_assets)),
            index=dates,
            columns=symbols,
        )
        self._sharpe = pd.Series(rng.uniform(0.3, 1.0, n_assets), index=symbols)
        self._describe = self._build_describe(symbols, rng)

    @staticmethod
    def _build_describe(symbols, rng):
        data = {
            "property": [
                "CAGR",
                "Risk",
                "CVAR",
                "Max drawdown",
                "Max dd date start",
                "Max dd date end",
                "Max dd days",
                "Dividend yield",
            ],
            "period": ["annually"] * 8,
        }
        for s in symbols:
            data[s] = rng.uniform(-0.05, 0.20, 8).tolist()
        return pd.DataFrame(data)

    def get_cumulative_return(self, real: bool = False) -> pd.DataFrame:
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

    def _adjust_price_to_currency_monthly(self, price: pd.Series, asset_currency: str) -> pd.Series:
        """Mirror of okama's private converter used by the RE page (guarded by
        tests/unit/test_macro_objects.py upgrade guard). RUB->USD divides by a
        fixed mock rate; same-currency passes through."""
        if self.currency == asset_currency:
            return price
        return price / 80.0


# ---------------------------------------------------------------------------
# Picklable mocks for okama macro classes (Inflation, Rate, Indicator, Asset).
# Real okama exposes every data member as a property; plain attributes give
# the same read surface and survive pickling. Only describe() is a method.
# first_date/last_date constructor params are accepted for API compatibility
# but ignored — mocks always serve the fixed 2020-01..2024-12 range, same as
# PicklablePortfolio/PicklableAssetList above.
# ---------------------------------------------------------------------------


def _monthly_period_series(symbol: str, base: float, scale: float) -> pd.Series:
    dates = pd.period_range("2020-01", "2024-12", freq="M")
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(base, scale, len(dates)), index=dates, name=symbol)


class PicklableInflation:
    """Mock for ok.Inflation: monthly fractions (~0.4%/month)."""

    def __init__(self, symbol: str = "RUB.INFL", first_date: str | None = None, last_date: str | None = None):
        self.symbol = symbol
        self.values_monthly = _monthly_period_series(symbol, base=0.004, scale=0.003)
        dates = self.values_monthly.index
        self.first_date = dates[0].to_timestamp()
        self.last_date = dates[-1].to_timestamp()
        self.cumulative_inflation = pd.Series(
            np.cumprod(1 + self.values_monthly.to_numpy()) - 1.0, index=dates, name=symbol
        )
        # Property on the real class: 12-month rolling compound inflation.
        # Mirrors okama's rolling-window product so the series starts at the
        # 12th month (2020-12), not one month later.
        self.rolling_inflation = ((self.values_monthly + 1.0).rolling(12).apply(np.prod, raw=True) - 1.0).dropna()
        annual_idx = pd.period_range("2020", "2024", freq="Y")
        rng = np.random.default_rng(7)
        self.annual_inflation_ts = pd.Series(rng.normal(0.05, 0.02, len(annual_idx)), index=annual_idx, name=symbol)
        self.purchasing_power_1000 = 785.0

    def describe(self, years: tuple = (1, 5, 10)) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "property": [
                    "compound inflation",
                    "1000 purchasing power",
                    "annual inflation",
                    "max 12m inflation",
                    "1000 purchasing power",
                ],
                "period": ["YTD", "YTD", "1 years", "2022-04", "1 years"],
                self.symbol: [0.031, 969.7, 0.056, 0.178, 947.0],
            }
        )


class PicklableRate:
    """Mock for ok.Rate: monthly rate fractions (~10%/year)."""

    def __init__(self, symbol: str = "RUS_CBR.RATE", first_date: str | None = None, last_date: str | None = None):
        self.symbol = symbol
        self.values_monthly = _monthly_period_series(symbol, base=0.10, scale=0.02)
        self.first_date = self.values_monthly.index[0].to_timestamp()
        self.last_date = self.values_monthly.index[-1].to_timestamp()

    def describe(self, years: tuple = (1, 5, 10)) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "property": ["arithmetic mean", "median value", "max value", "min value"],
                "period": ["YTD", "YTD", "2024-10", "2021-07"],
                self.symbol: [0.15, 0.1475, 0.21, 0.065],
            }
        )


class PicklableIndicator:
    """Mock for ok.Indicator: raw decimal values (CAPE10-like, ~25)."""

    def __init__(self, symbol: str = "USA_CAPE10.RATIO", first_date: str | None = None, last_date: str | None = None):
        self.symbol = symbol
        self.values_monthly = _monthly_period_series(symbol, base=25.0, scale=4.0)
        self.first_date = self.values_monthly.index[0].to_timestamp()
        self.last_date = self.values_monthly.index[-1].to_timestamp()

    def describe(self, years: tuple = (1, 5, 10)) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "property": ["arithmetic mean", "median value", "max value", "min value"],
                "period": ["YTD", "YTD", "2000-03", "1982-07"],
                self.symbol: [38.67, 39.21, 47.13, 8.06],
            }
        )


class PicklableAsset:
    """Mock for ok.Asset (RE namespace): per-m² prices in native RUB."""

    def __init__(self, symbol: str = "MOW_PR.RE", *args, **kwargs):
        self.symbol = symbol
        self.currency = "RUB"
        dates = pd.period_range("2020-01", "2024-12", freq="M")
        rng = np.random.default_rng(42)
        # A drifting price level around 250k RUB/m².
        self.close_monthly = pd.Series(
            250_000 * np.cumprod(1 + rng.normal(0.005, 0.01, len(dates))), index=dates, name=symbol
        )
        self.first_date = dates[0].to_timestamp()
        self.last_date = dates[-1].to_timestamp()


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

    cum_return_data = np.cumprod(1 + ror_data, axis=0) - 1.0
    mock.get_cumulative_return = MagicMock(return_value=pd.DataFrame(cum_return_data, index=dates, columns=symbols))
    mock.get_rolling_cagr = MagicMock(
        return_value=pd.DataFrame(rng.normal(0.08, 0.02, (n, n_assets)), index=dates, columns=symbols)
    )
    mock.get_sharpe_ratio = MagicMock(return_value=pd.Series(rng.uniform(0.3, 1.0, n_assets), index=symbols))

    describe_data = {
        "property": [
            "CAGR",
            "Risk",
            "CVAR",
            "Max drawdown",
            "Max dd date start",
            "Max dd date end",
            "Max dd days",
            "Dividend yield",
        ],
        "period": ["annually"] * 8,
    }
    for s in symbols:
        describe_data[s] = rng.uniform(-0.05, 0.20, 8).tolist()
    mock.describe = MagicMock(return_value=pd.DataFrame(describe_data))

    mock.inflation_ts = pd.Series(dtype=float)

    ts_data = rng.normal(0.0, 0.02, (n, max(n_assets - 1, 1)))
    ts_cols = symbols[1:] if n_assets > 1 else symbols
    mock.tracking_difference = MagicMock(return_value=pd.DataFrame(ts_data, index=dates, columns=ts_cols))
    mock.tracking_difference_annualized = MagicMock(return_value=pd.DataFrame(ts_data, index=dates, columns=ts_cols))

    annual_dates = pd.period_range("2020", "2024", freq="Y")
    annual_data = rng.normal(0.0, 0.03, (len(annual_dates), max(n_assets - 1, 1)))
    mock.tracking_difference_annual = pd.DataFrame(annual_data, index=annual_dates, columns=ts_cols)

    # AssetList.annual_return_ts is a property returning a DataFrame (one column per asset)
    mock.annual_return_ts = pd.DataFrame(
        rng.normal(0.05, 0.1, (len(annual_dates), n_assets)),
        index=annual_dates,
        columns=symbols,
    )

    mock.tracking_error = MagicMock(return_value=pd.DataFrame(np.abs(ts_data), index=dates, columns=ts_cols))
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

    # Mirrors okama 2.1.1: Portfolio.get_cumulative_return returns an expanding
    # time series with the portfolio column only (plus inflation if enabled).
    cum_return_data = np.cumprod(1 + rng.normal(0.005, 0.03, (n, 1)), axis=0) - 1.0
    mock.get_cumulative_return.return_value = pd.DataFrame(
        cum_return_data,
        index=dates,
        columns=["TestPF.PF"],
    )
    mock.get_rolling_cagr.return_value = pd.DataFrame(
        rng.normal(0.08, 0.02, (n, 3)),
        index=dates,
        columns=["TestPF.PF", "AAPL.US", "MSFT.US"],
    )
    mock.get_sharpe_ratio.return_value = 0.65

    # Portfolio.annual_return_ts is a method returning a Series (one value per year)
    annual_dates = pd.period_range("2020", "2024", freq="Y")
    mock.annual_return_ts.return_value = pd.Series(
        rng.normal(0.05, 0.1, len(annual_dates)),
        index=annual_dates,
        name="TestPF.PF",
    )

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
    dcf.monte_carlo_irr.return_value = pd.Series([0.04, 0.05, 0.06])
    dcf.irr.return_value = 0.045
    mock.dcf = dcf

    return mock

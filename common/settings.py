from functools import cache

import okama

default_symbols = []
default_benchmark = "SP500TR.INDX"
default_symbols_benchmark = []
default_currency = "USD"


@cache
def get_namespaces() -> list[str]:
    return okama.assets_namespaces


MONTHS_PER_YEAR = 12
MC_EF_MAX = 1000  # Max points in Monte-Carlo simulation in Efficient Frontier
MC_PORTFOLIO_MAX = 500  # Max wealth time series in Monte-Carlo simulation in Portfolio
MC_PORTFOLIO_YEARS_MAX = 50  # Max forecast period (years) in Portfolio Monte-Carlo simulation
MC_PORTFOLIO_BUDGET = 15_000  # Max simulations × forecast years per Portfolio request
ALLOWED_NUMBER_OF_TICKERS = 12  # max number of tickers in portfolio, EF or AssetList
RISK_FREE_RATE_DEFAULT = 0.05
INITIAL_INVESTMENT_DEFAULT = 1000

EF_POINTS = 80
GRID_POINT_BUDGET = 5000  # Max grid portfolios per request
GRID_ALLOWED_STEPS = (0.10, 0.20, 0.25, 0.50)  # Explicit grid weight steps (>= 10%)

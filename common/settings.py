import okama

default_symbols = []
default_benchmark = "SP500TR.INDX"
default_symbols_benchmark = []
default_currency = "USD"
namespaces = okama.assets_namespaces

MONTHS_PER_YEAR = 12
MC_EF_MAX = 5000  # Max points in Monte-Carlo simulation in Efficient Frontier
MC_PORTFOLIO_MAX = 30  # Max wealth time series in Monte-Carlo simulation in Portfolio
ALLOWED_NUMBER_OF_TICKERS = 12  # max number of tickers in portfolio, EF or AssetList

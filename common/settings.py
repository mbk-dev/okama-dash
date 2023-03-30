import okama

default_symbols = ["SPY.US", "BND.US", "GLD.US"]
default_benchmark = "SP500TR.INDX"
default_symbols_benchmark = ["SPY.US", "VOO.US"]
default_currency = "USD"
namespaces = okama.assets_namespaces

MONTHS_PER_YEAR = 12
MC_MAX = 10000  # Max points in Monte-Carlo simulation
ALLOWED_NUMBER_OF_TICKERS = 12  # max number of tickers in portfolio, EF or AssetList

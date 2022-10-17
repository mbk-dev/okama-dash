import io
from typing import Optional

import pandas as pd


def get_tickers_list(tickers: Optional[str]) -> Optional[list]:
    """
    Get tickers list from query (comma separated).
    """
    if tickers:
        tickers_io = io.StringIO(tickers)
        return pd.read_csv(tickers_io).columns.to_list()
    else:
        return None

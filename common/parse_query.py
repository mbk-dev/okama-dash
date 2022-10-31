import io
from typing import Optional

import pandas as pd


def make_list_from_string(symbols: Optional[str], char_type: str = "str") -> Optional[list]:
    """
    Get list of parameters from URL query (csv - comma separated).
    """
    if symbols:
        tickers_io = io.StringIO(symbols)
        df = pd.read_csv(tickers_io, header=None, dtype=char_type)
        result = df.iloc[0, :].to_list()
    else:
        result = None
    return result

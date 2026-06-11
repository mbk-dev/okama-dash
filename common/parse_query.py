import io
from typing import Optional

import pandas as pd


def make_list_from_string(symbols: Optional[str], char_type: str = "str") -> Optional[list]:
    """
    Get list of parameters from URL query (csv - comma separated).
    """
    if symbols:
        tickers_io = io.StringIO(symbols)
        try:
            df = pd.read_csv(tickers_io, header=None, dtype=char_type)
        except ValueError:
            # Malformed value in a hand-edited link (e.g. weights=34.33.33):
            # fall back to defaults instead of crashing the page layout.
            return None
        result = df.iloc[0, :].to_list()
    else:
        result = None
    return result

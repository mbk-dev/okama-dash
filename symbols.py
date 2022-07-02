from functools import lru_cache

import pandas as pd
import okama as ok


@lru_cache()
def get_symbols() -> list:
    """
    Get all available symbols (tickers) from assets namespaces.
    """
    namespaces = ['US', 'LSE', 'MOEX', 'INDX', 'COMM', 'FX', 'CC']
    list_of_symbols = [ok.symbols_in_namespace(ns) for ns in namespaces]
    classifier_df = pd.concat(list_of_symbols,
                          axis=0,
                          join="outer",
                          copy="false",
                          ignore_index=True)
    return classifier_df.symbol.to_list()

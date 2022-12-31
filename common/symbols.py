import pandas as pd
import okama as ok

from common import cache
import common.settings as settings


@cache.memoize(timeout=2592000)
def get_symbols() -> list:
    """
    Get all available symbols (tickers) from assets namespaces.
    """
    list_of_symbols = [ok.symbols_in_namespace(ns).symbol for ns in settings.namespaces]
    classifier_df = pd.concat(list_of_symbols, axis=0, join="outer", copy="false", ignore_index=True)
    return classifier_df.to_list()


def get_symbols_names() -> dict:
    """
    Get a dictionary of long_name + symbol values.
    """
    namespaces = ok.assets_namespaces
    list_of_symbols = [ok.symbols_in_namespace(ns).loc[:, ["symbol", "name"]] for ns in namespaces]
    classifier_df = pd.concat(list_of_symbols, axis=0, join="outer", copy="false", ignore_index=True)
    classifier_df["long_name"] = classifier_df.symbol + " : " + classifier_df.name
    return classifier_df.loc[:, ["long_name", "symbol"]].to_dict("records")

from functools import lru_cache

import okama as ok


@lru_cache()
def get_currency_list():
    inflation_list = ok.symbols_in_namespace("INFL").symbol.tolist()
    return [x.split(".", 1)[0] for x in inflation_list]

import okama as ok


def get_currency_list():
    inflation_list = ok.symbols_in_namespace("INFL").symbol.tolist()
    return [x.split(".", 1)[0] for x in inflation_list]

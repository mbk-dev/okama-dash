import okama as ok


def get_currency_list():
    inflation_list = ok.symbols_in_namespace("INFL").symbol.tolist()
    return [x.split(".", 1)[0] for x in inflation_list]


def resolve_url_currency(ccy: str | None, currency_list: list[str], default: str = "USD") -> str:
    """Currency dropdown value for a URL-prefilled form.

    Case-insensitive; a value missing from the known currency list falls back
    to the default, so the dropdown is never cleared client-side
    (dcc.Dropdown silently drops a value absent from its options).
    """
    candidate = ccy.upper() if ccy else None
    return candidate if candidate in currency_list else default

import okama as ok

from common import cache
from common.symbols import _data_source_token


def get_currency_list():
    return _build_currency_list(_data_source_token())


@cache.memoize(timeout=2592000)
def _build_currency_list(token: str) -> list[str]:
    """Currency codes from the INFL namespace, cached for 30 days.

    New currencies appear rarely, so one okama API call per month is enough.
    ``token`` keeps mocked (TESTING=1) and real data in separate cache slots
    and rolls the cache over on okama upgrades (same discipline as the symbol
    indices in common/symbols.py).
    """
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

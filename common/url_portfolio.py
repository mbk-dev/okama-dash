"""Portfolio-from-URL helpers shared by the Compare and Benchmark pages.

The Portfolio page hands its portfolio off via a self-contained URL param
group (pf_tickers/pf_weights/pf_rebal/pf_symbol — issue #23). The group is
parsed once at layout time into a dcc.Store; the portfolio then shows up as
a synthetic chip (its symbol) inside the page's tickers MultiSelect.
"""

import re

from common.parse_query import make_list_from_string

PF_REBAL_DEFAULT = "month"
PF_SYMBOL_DEFAULT = "PORTFOLIO"

# Anything outside this set is replaced in cache tokens: the token lands in a
# pickle FILENAME via object_cache._build_cache_key's f-string interpolation.
_CACHE_KEY_UNSAFE = re.compile(r"[^A-Za-z0-9_.,:;-]")


def normalize_portfolio_symbol(symbol: str) -> str:
    """Portfolio-page symbol rules: spaces to underscores, .PF suffix appended."""
    symbol = symbol.replace(" ", "_")
    return symbol + ".PF" if not symbol.lower().endswith(".pf") else symbol


def parse_url_portfolio_group(
    pf_tickers: str | None, pf_weights: str | None, pf_rebal: str | None = None, pf_symbol: str | None = None
) -> dict | None:
    """Parse the pf_* URL param group into store data.

    Returns None when the group is absent or invalid (unparseable weights,
    count mismatch, sum far from 100): a broken group must never break the
    page — the link then behaves like a plain one (EF-handoff behavior).
    """
    if not pf_tickers or not pf_weights:
        return None
    tickers_list = make_list_from_string(pf_tickers)
    try:
        weights_list = make_list_from_string(pf_weights, char_type="float")
    except (ValueError, TypeError):
        return None
    if not tickers_list or not weights_list or len(weights_list) != len(tickers_list):
        return None
    # Inverted comparison so a NaN sum (empty CSV field) also fails the check.
    if not abs(sum(weights_list) - 100.0) < 1e-6:
        return None
    return {
        "tickers": tickers_list,
        "weights": weights_list,
        "rebal": pf_rebal or PF_REBAL_DEFAULT,
        "symbol": normalize_portfolio_symbol(pf_symbol or PF_SYMBOL_DEFAULT),
    }


def split_portfolio_from_selection(values: list | None, pf_def: dict | None) -> tuple[list, bool]:
    """Split MultiSelect values into (real tickers, portfolio-chip present).

    The chip is recognized by exact match against the store's symbol — the
    single recognition point for every consumer of the tickers list.
    """
    values = [v for v in (values or []) if v]
    token = (pf_def or {}).get("symbol")
    if not token:
        return values, False
    tickers = [v for v in values if v != token]
    return tickers, len(tickers) != len(values)


def portfolio_option(pf_def: dict) -> dict:
    """Synthetic MultiSelect option for the portfolio chip.

    Must be present in the select's data whenever the chip is in its value,
    or dmc renders no chip; keeping it in search results also makes the chip
    re-addable after removal.
    """
    return {"value": pf_def["symbol"], "label": pf_def["symbol"]}


def pf_link_kwargs(pf_def: dict) -> dict:
    """create_link kwargs for the pf_* group; the default symbol is omitted
    (link diet): the parsed store holds the normalized form (PORTFOLIO.PF),
    which would otherwise dodge create_link's skip-if-default "PORTFOLIO"."""
    symbol = pf_def["symbol"]
    return {
        "pf_tickers": pf_def["tickers"],
        "pf_weights": pf_def["weights"],
        "pf_rebal": pf_def["rebal"],
        "pf_symbol": None if symbol == normalize_portfolio_symbol(PF_SYMBOL_DEFAULT) else symbol,
    }


def pf_cache_token(pf_def: dict | None) -> str | None:
    """Compact filename-safe discriminator for object-cache keys: an AssetList
    with the URL portfolio must not share a cache slot with the plain one."""
    if not pf_def:
        return None
    pairs = ",".join(f"{t}:{w:g}" for t, w in zip(pf_def["tickers"], pf_def["weights"], strict=True))
    return _CACHE_KEY_UNSAFE.sub("_", f"{pairs};{pf_def['rebal']};{pf_def['symbol']}")

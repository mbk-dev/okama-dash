"""Portfolio-from-URL helpers shared by the Compare and Benchmark pages.

The Portfolio page hands its portfolio off via a self-contained URL param
group (pf_tickers/pf_weights/pf_rebal/pf_symbol — issue #23). The group is
parsed once at layout time into a dcc.Store; the portfolio then shows up as
a synthetic chip (its symbol) inside the page's tickers MultiSelect.
"""

import re

import okama as ok

from common.object_cache import TTL_PORTFOLIO, get_or_create
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
    pf_tickers: str | None,
    pf_weights: str | None,
    pf_rebal: str | None = None,
    pf_symbol: str | None = None,
    pf_abs_dev: str | None = None,
    pf_rel_dev: str | None = None,
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

    def _opt_float(v):
        if v in (None, ""):
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    return {
        "tickers": tickers_list,
        "weights": weights_list,
        "rebal": pf_rebal or PF_REBAL_DEFAULT,
        "symbol": normalize_portfolio_symbol(pf_symbol or PF_SYMBOL_DEFAULT),
        "abs_dev": _opt_float(pf_abs_dev),
        "rel_dev": _opt_float(pf_rel_dev),
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
        "pf_abs_dev": pf_def.get("abs_dev"),
        "pf_rel_dev": pf_def.get("rel_dev"),
    }


def pf_cache_token(pf_def: dict | None) -> str | None:
    """Compact filename-safe discriminator for object-cache keys: an AssetList
    with the URL portfolio must not share a cache slot with the plain one."""
    if not pf_def:
        return None
    pairs = ",".join(f"{t}:{w:g}" for t, w in zip(pf_def["tickers"], pf_def["weights"], strict=True))
    token = f"{pairs};{pf_def['rebal']};{pf_def['symbol']}"
    abs_dev = pf_def.get("abs_dev")
    rel_dev = pf_def.get("rel_dev")
    # Append deviations only when at least one is present, so tokens for
    # deviation-less portfolios stay byte-identical (existing cache slots).
    # :g strips the trailing .0 of float store values (same as the weights above).
    if abs_dev is not None or rel_dev is not None:
        abs_part = f"{abs_dev:g}" if abs_dev is not None else ""
        rel_part = f"{rel_dev:g}" if rel_dev is not None else ""
        token += f";{abs_part};{rel_part}"
    return _CACHE_KEY_UNSAFE.sub("_", token)


def get_or_create_url_portfolio(pf_def: dict, *, ccy: str, first_date: str, last_date: str) -> ok.Portfolio:
    """Cached ok.Portfolio built from the parsed pf_* group.

    Same object-cache pattern as the EF handoff (ef_cache.get_portfolio_point),
    but returns the object itself: it goes into ok.AssetList as an asset.
    inflation=False is correct inside AssetList(inflation=True) — the AssetList
    computes inflation itself.
    """
    weights = [w / 100.0 for w in pf_def["weights"]]
    abs_dev = pf_def.get("abs_dev")
    rel_dev = pf_def.get("rel_dev")

    def _construct() -> ok.Portfolio:
        return ok.Portfolio(
            assets=pf_def["tickers"],
            weights=weights,
            ccy=ccy,
            first_date=first_date,
            last_date=last_date,
            inflation=False,
            # Deviations are raw percentages in the store; okama wants fractions.
            rebalancing_strategy=ok.Rebalance(
                period=pf_def["rebal"],
                abs_deviation=abs_dev / 100.0 if abs_dev else None,
                rel_deviation=rel_dev / 100.0 if rel_dev else None,
            ),
            symbol=pf_def["symbol"],
        )

    pf, _ = get_or_create(
        obj_type="portfolio",
        constructor_fn=_construct,
        # pf_cache_token (sanitized) identifies tickers+weights+rebal+symbol in
        # one filename-safe value: raw URL-controlled strings must never reach
        # the pickle filename via _build_cache_key's f-string interpolation.
        cache_key_params={
            "ccy": ccy,
            "first_date": first_date,
            "last_date": last_date,
            "pf": pf_cache_token(pf_def),
            "purpose": "url_portfolio",
        },
        ttl_seconds=TTL_PORTFOLIO,
    )
    return pf

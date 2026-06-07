"""Cached accessors for okama macro objects (Inflation, Rate, Indicator).

One get_or_create wrapping point per class keeps cache keys consistent across
pages (the inflation page's key-rate overlay and the rates page share the same
cached ok.Rate pickles) and gives tests a single patch target.
"""

import okama as ok

from common.object_cache import TTL_ASSET_LIST, get_or_create


def get_inflation_object(symbol: str, first_date: str | None, last_date: str | None) -> ok.Inflation:
    obj, _ = get_or_create(
        obj_type="inflation",
        constructor_fn=lambda: ok.Inflation(symbol, first_date=first_date, last_date=last_date),
        cache_key_params={"symbols": [symbol], "first_date": first_date, "last_date": last_date},
        ttl_seconds=TTL_ASSET_LIST,
    )
    return obj


def get_rate_object(symbol: str, first_date: str | None, last_date: str | None) -> ok.Rate:
    obj, _ = get_or_create(
        obj_type="rate",
        constructor_fn=lambda: ok.Rate(symbol, first_date=first_date, last_date=last_date),
        cache_key_params={"symbols": [symbol], "first_date": first_date, "last_date": last_date},
        ttl_seconds=TTL_ASSET_LIST,
    )
    return obj


def get_indicator_object(symbol: str, first_date: str | None, last_date: str | None) -> ok.Indicator:
    obj, _ = get_or_create(
        obj_type="indicator",
        constructor_fn=lambda: ok.Indicator(symbol, first_date=first_date, last_date=last_date),
        cache_key_params={"symbols": [symbol], "first_date": first_date, "last_date": last_date},
        ttl_seconds=TTL_ASSET_LIST,
    )
    return obj


def get_asset_object(symbol: str) -> ok.Asset:
    """Cached single asset (RE namespace): native-currency prices, full history.

    Deliberately takes no dates — the RE page trims/masks series itself, so one
    full-history pickle per symbol serves every date selection.
    """
    obj, _ = get_or_create(
        obj_type="asset",
        constructor_fn=lambda: ok.Asset(symbol),
        cache_key_params={"symbols": [symbol]},
        ttl_seconds=TTL_ASSET_LIST,
    )
    return obj


def get_asset_list_object(
    symbols: list[str],
    ccy: str,
    first_date: str | None,
    last_date: str | None,
    inflation: bool = False,
) -> ok.AssetList:
    obj, _ = get_or_create(
        obj_type="assetlist",
        constructor_fn=lambda: ok.AssetList(
            symbols, ccy=ccy, first_date=first_date, last_date=last_date, inflation=inflation
        ),
        cache_key_params={
            "symbols": symbols,
            "ccy": ccy,
            "first_date": first_date,
            "last_date": last_date,
            "inflation": inflation,
        },
        ttl_seconds=TTL_ASSET_LIST,
    )
    return obj

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

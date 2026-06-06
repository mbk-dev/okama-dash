import inspect

import numpy as np
import okama as ok

from common import cache, settings
from common.object_cache import (
    TTL_EFFICIENT_FRONTIER,
    TTL_PORTFOLIO,
    get_okama_version,
    get_or_create,
    load_cached,
)

CACHE_TIMEOUT = 2592000
DERIVED_CACHE_VERSION = f"ef-derived-v1-okv={get_okama_version()}"


def get_or_create_ef_object(
    symbols: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    rebalancing_period: str,
) -> tuple[ok.EfficientFrontier, str]:
    def _construct() -> ok.EfficientFrontier:
        ef_kwargs: dict = {
            "first_date": first_date,
            "last_date": last_date,
            "ccy": ccy,
            "inflation": False,
            "n_points": settings.EF_POINTS,
            "full_frontier": True,
        }
        sig = inspect.signature(ok.EfficientFrontier)
        if "rebalancing_strategy" in sig.parameters:
            ef_kwargs["rebalancing_strategy"] = ok.Rebalance(period=rebalancing_period)
        ef = ok.EfficientFrontier(symbols, **ef_kwargs)
        _ = ef.ef_points
        return ef

    return get_or_create(
        obj_type="ef",
        constructor_fn=_construct,
        cache_key_params={
            "symbols": symbols,
            "ccy": ccy,
            "first_date": first_date,
            "last_date": last_date,
            "rebal": rebalancing_period,
            "efp": settings.EF_POINTS,
        },
        ttl_seconds=TTL_EFFICIENT_FRONTIER,
    )


def load_ef_object(file_name: str) -> ok.EfficientFrontier:
    return load_cached(file_name)


def get_portfolio_point(
    symbols: list[str],
    weights_percent: list[float],
    ccy: str,
    first_date: str,
    last_date: str,
    rebalancing_period: str,
) -> dict:
    """Risk/CAGR coordinates (in percent) for the portfolio passed in the URL.

    Builds (or loads from the object cache) an ok.Portfolio with the same
    universe and settings as the frontier; the point is therefore directly
    comparable with ef_points on both axes.
    """
    weights = [w / 100.0 for w in weights_percent]

    def _construct() -> ok.Portfolio:
        return ok.Portfolio(
            assets=symbols,
            weights=weights,
            ccy=ccy,
            first_date=first_date,
            last_date=last_date,
            inflation=False,
            rebalancing_strategy=ok.Rebalance(period=rebalancing_period),
        )

    pf, _ = get_or_create(
        obj_type="portfolio",
        constructor_fn=_construct,
        cache_key_params={
            "symbols": symbols,
            "weights": weights,
            "ccy": ccy,
            "first_date": first_date,
            "last_date": last_date,
            "rebal": rebalancing_period,
            "purpose": "ef_point",
        },
        ttl_seconds=TTL_PORTFOLIO,
    )
    return {
        "risk": float(pf.risk_annual.iloc[-1]) * 100,
        "cagr": float(pf.get_cagr().iloc[-1][pf.symbol]) * 100,
    }


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_minimized_risk_portfolio_cached(cache_version: str, file_name: str, target_value: float) -> dict:
    del cache_version
    ef_object = load_cached(file_name)
    optimized_portfolio = ef_object.minimize_risk(target_value=target_value)
    return {
        key: value.tolist() if isinstance(value, np.ndarray) else value
        for key, value in optimized_portfolio.items()
    }


def get_minimized_risk_portfolio(file_name: str, target_value: float) -> dict:
    return _get_minimized_risk_portfolio_cached(DERIVED_CACHE_VERSION, file_name, target_value)

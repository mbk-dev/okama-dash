import inspect
import os
import pickle
import platform
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import okama as ok

import common
import common.create_link
from common import cache, settings

CACHE_TIMEOUT = 2592000
BASE_CACHE_VERSION = "ef-base-v2"
DERIVED_CACHE_VERSION = "ef-derived-v1"
FILE_CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
FILE_CACHE_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60
data_folder = Path(__file__).parent.parent.parent / common.cache_directory
cleanup_marker_file = data_folder / ".ef-base-cache-cleanup"
cleanup_lock_file = data_folder / ".ef-base-cache-cleanup.lock"


def build_ef_file_name(
    symbols: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    rebalancing_period: str,
) -> str:
    base_file_name = common.create_link.create_filename(
        tickers_list=symbols,
        ccy=ccy,
        first_date=first_date,
        last_date=last_date,
        rebal=rebalancing_period,
    )
    stem, suffix = base_file_name.rsplit(".", maxsplit=1)
    return f"{stem}-efp={settings.EF_POINTS}-cv={BASE_CACHE_VERSION}.{suffix}"


def _build_ef_kwargs(
    ccy: str,
    first_date: str,
    last_date: str,
    rebalancing_period: str,
) -> dict:
    ef_kwargs = dict(
        first_date=first_date,
        last_date=last_date,
        ccy=ccy,
        inflation=False,
        n_points=settings.EF_POINTS,
        full_frontier=True,
    )
    ef_signature = inspect.signature(ok.EfficientFrontier)
    if "rebalancing_strategy" in ef_signature.parameters:
        ef_kwargs["rebalancing_strategy"] = ok.Rebalance(period=rebalancing_period)
    return ef_kwargs


def _is_linux_environment() -> bool:
    return platform.system() == "Linux"


def _is_ef_base_cache_file(path: Path) -> bool:
    return path.suffix == ".pkl" and "-cv=ef-base-v" in path.name


def _cleanup_expired_ef_cache_files_if_needed() -> None:
    if not _is_linux_environment():
        return
    data_folder.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if cleanup_marker_file.exists():
        marker_age = now - cleanup_marker_file.stat().st_mtime
        if marker_age < FILE_CACHE_CLEANUP_INTERVAL_SECONDS:
            return
    try:
        lock_fd = os.open(str(cleanup_lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return
    try:
        os.close(lock_fd)
        if cleanup_marker_file.exists():
            marker_age = now - cleanup_marker_file.stat().st_mtime
            if marker_age < FILE_CACHE_CLEANUP_INTERVAL_SECONDS:
                return
        expiration_threshold = now - FILE_CACHE_TTL_SECONDS
        for path in data_folder.glob("*.pkl"):
            if not _is_ef_base_cache_file(path):
                continue
            try:
                if path.stat().st_mtime < expiration_threshold:
                    path.unlink(missing_ok=True)
            except FileNotFoundError:
                continue
        cleanup_marker_file.touch()
    finally:
        cleanup_lock_file.unlink(missing_ok=True)


def store_ef_object(file_name: str, ef_object: ok.EfficientFrontier) -> None:
    with open(data_folder / file_name, "wb") as file:
        pickle.dump(ef_object, file, protocol=pickle.HIGHEST_PROTOCOL)
    _load_ef_object_from_file.cache_clear()


def load_ef_object(file_name: str) -> ok.EfficientFrontier:
    data_file = data_folder / file_name
    return _load_ef_object_from_file(file_name, data_file.stat().st_mtime_ns)


@lru_cache(maxsize=32)
def _load_ef_object_from_file(file_name: str, mtime_ns: int) -> ok.EfficientFrontier:
    del mtime_ns
    with open(data_folder / file_name, "rb") as file:
        return pickle.load(file)


@cache.memoize(timeout=CACHE_TIMEOUT)
def _get_minimized_risk_portfolio_cached(cache_version: str, file_name: str, target_value: float) -> dict:
    del cache_version
    ef_object = load_ef_object(file_name)
    optimized_portfolio = ef_object.minimize_risk(target_value=target_value)

    normalized_portfolio = {}
    for key, value in optimized_portfolio.items():
        if isinstance(value, np.ndarray):
            normalized_portfolio[key] = value.tolist()
        else:
            normalized_portfolio[key] = value
    return normalized_portfolio


def get_minimized_risk_portfolio(file_name: str, target_value: float) -> dict:
    return _get_minimized_risk_portfolio_cached(DERIVED_CACHE_VERSION, file_name, target_value)


def get_or_create_ef_object(
    symbols: list[str],
    ccy: str,
    first_date: str,
    last_date: str,
    rebalancing_period: str,
) -> tuple[ok.EfficientFrontier, str]:
    _cleanup_expired_ef_cache_files_if_needed()
    file_name = build_ef_file_name(
        symbols=symbols,
        ccy=ccy,
        first_date=first_date,
        last_date=last_date,
        rebalancing_period=rebalancing_period,
    )
    data_file = data_folder / file_name
    if data_file.is_file():
        return load_ef_object(file_name), file_name

    ef_object = ok.EfficientFrontier(
        symbols,
        **_build_ef_kwargs(
            ccy=ccy,
            first_date=first_date,
            last_date=last_date,
            rebalancing_period=rebalancing_period,
        ),
    )
    _ = ef_object.ef_points
    store_ef_object(file_name, ef_object)
    return ef_object, file_name

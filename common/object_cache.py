import fcntl
import hashlib
import logging
import os
import pickle
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, TypeVar

import okama

T = TypeVar("T")

logger = logging.getLogger("object_cache")

CACHE_FORMAT_VERSION = "obj-v1"

# A single path component must not exceed the filesystem limit (NAME_MAX,
# 255 bytes on ext4/tmpfs). Long ticker lists plus cashflow params can push
# the descriptive cache filename past it.
_MAX_FILENAME_BYTES = 255

TTL_ASSET_LIST = 7 * 24 * 3600
TTL_PORTFOLIO = 7 * 24 * 3600
TTL_EFFICIENT_FRONTIER = 30 * 24 * 3600

_CLEANUP_INTERVAL_SECONDS = 24 * 3600

_cache_dir = Path(__file__).parent.parent / "cache-directory"


def _data_source_token() -> str:
    """
    Discriminator that keeps mocked and real object data in separate cache slots.

    Portfolio and AssetList pickles are cached for up to 30 days. When the app
    runs with mocked okama (``TESTING=1``, e.g. during E2E tests) it must not
    share a cache key with the real app — otherwise the real app would serve
    pickles built from mock data. The okama version also invalidates the cache
    when the upstream dataset changes.
    """
    if os.environ.get("TESTING") == "1":
        return "test"
    return getattr(okama, "__version__", "unknown")


def get_okama_version() -> str:
    return okama.__version__


def _build_cache_key(obj_type: str, cache_key_params: dict[str, Any]) -> str:
    symbols = list(cache_key_params.get("symbols", []))
    weights = cache_key_params.get("weights")

    if weights and symbols:
        paired = sorted(zip(symbols, weights, strict=True), key=lambda x: x[0])
        symbols = [s for s, _ in paired]
        weights = [w for _, w in paired]
    else:
        symbols = sorted(symbols)

    parts = [obj_type, "-".join(symbols)]

    skip_keys = {"symbols", "weights"}
    for key in sorted(cache_key_params.keys()):
        if key in skip_keys:
            continue
        value = cache_key_params[key]
        if value is not None:
            parts.append(f"{key}={value}")

    if weights:
        parts.append(f"w={','.join(str(w) for w in weights)}")

    parts.append(f"okv={_data_source_token()}")
    parts.append(f"cv={CACHE_FORMAT_VERSION}")
    name = "-".join(parts) + ".pkl"

    if len(name.encode("utf-8")) > _MAX_FILENAME_BYTES:
        # Fall back to a hashed name so the cache still persists. Keep the
        # obj_type prefix for debuggability and the cv marker so
        # cleanup_expired_files() still sweeps the file.
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        name = f"{obj_type}-{digest}-cv={CACHE_FORMAT_VERSION}.pkl"
    return name


def _atomic_write(file_path: Path, obj: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        fd_int, tmp_path_str = tempfile.mkstemp(
            dir=str(file_path.parent), suffix=".tmp", prefix=".cache-"
        )
        tmp_path = Path(tmp_path_str)
        with os.fdopen(fd_int, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_path.rename(file_path)
        tmp_path = None
    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def _safe_load(file_path: Path) -> Any:
    try:
        with open(file_path, "rb") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return pickle.load(f)  # noqa: S301
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (pickle.UnpicklingError, EOFError, ModuleNotFoundError) as exc:
        logger.warning("Corrupt cache file %s: %s. Removing.", file_path, exc)
        file_path.unlink(missing_ok=True)
        raise FileNotFoundError(f"Removed corrupt cache: {file_path}") from exc


@lru_cache(maxsize=64)
def _lru_load(cache_key: str, mtime_ns: int) -> Any:
    del mtime_ns
    return _safe_load(_cache_dir / cache_key)


def get_or_create(
    obj_type: str,
    constructor_fn: Callable[[], T],
    cache_key_params: dict[str, Any],
    ttl_seconds: int,
) -> tuple[T, str]:
    cleanup_expired_files()

    cache_key = _build_cache_key(obj_type, cache_key_params)
    file_path = _cache_dir / cache_key

    try:
        stat = file_path.stat()
        age = time.time() - stat.st_mtime
        if age < ttl_seconds:
            obj = _lru_load(cache_key, stat.st_mtime_ns)
            logger.info("cache_hit obj_type=%s key=%s age=%.0fs", obj_type, cache_key, age)
            return obj, cache_key
        else:
            logger.info("cache_expired obj_type=%s key=%s age=%.0fs", obj_type, cache_key, age)
    except FileNotFoundError:
        pass
    except Exception as exc:
        logger.warning("Cache load failed for %s: %s", cache_key, exc)

    obj = constructor_fn()

    try:
        _atomic_write(file_path, obj)
        logger.info("cache_store obj_type=%s key=%s size=%d", obj_type, cache_key, file_path.stat().st_size)
    except Exception as exc:
        logger.warning("Cache write failed for %s: %s", cache_key, exc)

    return obj, cache_key


def load_cached(cache_key: str) -> Any:
    file_path = _cache_dir / cache_key
    stat = file_path.stat()
    return _lru_load(cache_key, stat.st_mtime_ns)


def _should_skip_cleanup(marker: Path, lock_file: Path) -> bool:
    if marker.exists() and time.time() - marker.stat().st_mtime < _CLEANUP_INTERVAL_SECONDS:
        return True
    try:
        lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(lock_fd)
    except FileExistsError:
        return True
    return False


def cleanup_expired_files(max_ttl_seconds: int | None = None, *, _force: bool = False) -> None:
    max_ttl = max_ttl_seconds or max(TTL_ASSET_LIST, TTL_PORTFOLIO, TTL_EFFICIENT_FRONTIER)
    _cache_dir.mkdir(parents=True, exist_ok=True)

    marker = _cache_dir / ".object-cache-cleanup"
    lock_file = _cache_dir / ".object-cache-cleanup.lock"

    if not _force and _should_skip_cleanup(marker, lock_file):
        return

    try:
        threshold = time.time() - max_ttl
        removed = 0
        cv_pattern = f"cv={CACHE_FORMAT_VERSION}"
        for path in _cache_dir.glob("*.pkl"):
            if cv_pattern not in path.name:
                continue
            try:
                if path.stat().st_mtime < threshold:
                    path.unlink(missing_ok=True)
                    removed += 1
            except FileNotFoundError:
                continue
        if removed:
            logger.info("cache_cleanup removed=%d", removed)
        marker.touch()
    finally:
        if not _force:
            lock_file.unlink(missing_ok=True)

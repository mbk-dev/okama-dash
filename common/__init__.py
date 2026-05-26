import logging
import os

from flask_caching import Cache

cache_directory = "cache-directory"

_cache_backend = os.environ.get("OKAMA_CACHE_BACKEND", "redis")

if _cache_backend == "redis":
    logging.info("caching in redis")
    cache = Cache(
        config={
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": os.environ.get("OKAMA_REDIS_URL", "redis://localhost:6379/0"),
            "CACHE_DEFAULT_TIMEOUT": 500,
        },
    )
else:
    logging.info("caching in filesystem")
    cache = Cache(
        config={
            "CACHE_TYPE": "filesystem",
            "CACHE_DIR": cache_directory,
            "CACHE_DEFAULT_TIMEOUT": 500,
        },
    )

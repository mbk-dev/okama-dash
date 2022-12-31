from flask_caching import Cache

cache = Cache(
    # config={
    #     "CACHE_TYPE": "filesystem",
    #     "CACHE_DIR": "cache-directory",
    #     "CACHE_DEFAULT_TIMEOUT": 300,
    # },
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": "redis://localhost:6379/0",
        "CACHE_DEFAULT_TIMEOUT": 500,
    },

)

---
name: run-okama-dash
description: Run okama-dash locally for development or testing. Use when the user asks to start the app, run the dev server, launch okama-dash, or says "запусти", "run the app", "start dev server", "открой приложение", "запусти с моками". Also use when verifying changes in the browser or when the /run skill is invoked in this project.
---

# Run okama-dash locally

Start the Dash development server for okama-dash with the right environment
for local development.

## Quick start

Default mode — filesystem cache, no Redis needed, hot reload enabled:

```bash
OKAMA_CACHE_BACKEND=filesystem poetry run python app.py
```

App available at http://localhost:8050, `debug=True` enables hot reload.

## Modes

### Development (default)

Uses filesystem cache (`cache-directory/`), connects to real okama API for financial data.

```bash
OKAMA_CACHE_BACKEND=filesystem poetry run python app.py
```

Choose this when working on UI, styles, or callbacks that need real data.

### Testing with mocks

Uses mocked okama data — no external API calls, no Redis. Useful for working
on layout, controls, and callback wiring without waiting for API responses.

```bash
TESTING=1 OKAMA_CACHE_BACKEND=filesystem poetry run python app.py
```

Mock data comes from `tests/mocks/okama_mock.py` — `PicklablePortfolio` and
`PicklableAssetList` classes provide realistic but static financial data.

### With Redis cache

If Redis is running locally, omit `OKAMA_CACHE_BACKEND` to use the default Redis backend:

```bash
poetry run python app.py
```

Redis URL defaults to `redis://localhost:6379/0`, override with `OKAMA_REDIS_URL`.

## What to check after starting

1. Open http://localhost:8050 in the browser
2. Verify navigation — all 5 pages load: EF (`/`), Compare, Benchmark, Portfolio, Database
3. If testing a specific change, navigate to the relevant page and exercise the feature

## Stopping

`Ctrl+C` in the terminal. The Dash dev server shuts down cleanly.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Virtualenv not set up | `poetry install` |
| `ConnectionRefusedError` on Redis | Redis not running, cache backend is `redis` | Set `OKAMA_CACHE_BACKEND=filesystem` |
| Port 8050 already in use | Another instance running | Kill it: `lsof -ti:8050 \| xargs kill` |
| `okama` API timeout | Network issue or API down | Use `TESTING=1` mode |

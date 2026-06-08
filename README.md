[![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/mbk-dev/okama-dash)](https://github.com/mbk-dev/okama-dash/blob/master/LICENSE.md)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# Okama widgets

Interactive financial widgets — a multi-page web application built with the
[okama](https://github.com/mbk-dev/okama/) package and the [Dash (Plotly)](https://dash.plotly.com/) framework.

A live instance is running at **[okama.io](https://okama.io)**.

![Okama widgets — Efficient Frontier page](https://raw.githubusercontent.com/mbk-dev/okama-dash/images/images/main_page.jpg)

## Features

| Widget | Route | What it does |
|--------|-------|--------------|
| **Efficient Frontier** | `/` | Portfolio optimization: efficient frontier chart, assets transition map, simulated portfolios |
| **Compare assets** | `/compare` | Compare assets' historical performance: wealth indexes, rate of return, risk, CVAR, drawdowns, correlation |
| **Compare with benchmark** | `/benchmark` | Compare assets with a benchmark: tracking difference, tracking error, correlation, beta |
| **Investment Portfolio** | `/portfolio` | Portfolio analysis: rebalancing, cash flow strategies, Monte Carlo forecasts, find max withdrawal |
| **Database** | `/database` | Search the financial database: stocks, ETF, mutual funds, indexes, currencies, commodities, rates |
| **Macro indicators** | `/macro/*` | Macroeconomic charts: inflation, central-bank rates, CAPE10 valuation |

![Wealth indexes chart in the Compare widget](https://raw.githubusercontent.com/mbk-dev/okama-dash/images/images/wealth_indexes.png)

## Getting started

### Prerequisites

- [Python](https://www.python.org/) 3.11+
- [Poetry](https://python-poetry.org/docs/) for dependency management (recommended)

### Installation

```bash
git clone https://github.com/mbk-dev/okama-dash.git
cd okama-dash
poetry install
```

Alternatively, with pip:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally

```bash
poetry run python app.py
```

The development server starts at <http://localhost:8050>.

> [!NOTE]
> By default the application caches okama data in Redis. To run without Redis, set
> `OKAMA_CACHE_BACKEND=filesystem` — caching falls back to the local `cache-directory/` folder.

| Environment variable | Default | Description |
|----------------------|---------|-------------|
| `OKAMA_CACHE_BACKEND` | `redis` | Cache backend: `redis` or `filesystem` |
| `OKAMA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (used when the backend is `redis`) |

## Production

For production, serve the application with [Gunicorn](https://gunicorn.org/) (installed by `poetry install`)
using the `run_gunicorn.py` entry point:

```bash
poetry run gunicorn run_gunicorn:server
```

## Historical data

The widgets use free "end of day" historical data and macroeconomic indicators provided by the
[okama](https://github.com/mbk-dev/okama/) package:

- Stocks, ETF and mutual funds for main world markets
- Stock indexes and commodities
- FX and crypto currencies, central bank exchange rates
- Macroeconomic indicators (inflation, central bank rates, CAPE10) for many countries

See the [okama package](https://github.com/mbk-dev/okama/) for the full data coverage.

## Tests

```bash
poetry run pytest -m "not e2e"   # fast suite: unit + component tests
poetry run pytest -q             # everything, including browser (e2e) tests
```

Unit and component tests mock the okama API — no network access or Redis required.
The e2e tests run in a real browser; install it once with `poetry run playwright install chromium`.

## Related projects

- [okama](https://github.com/mbk-dev/okama) — Python package for investment portfolio analysis, the engine behind these widgets
- [okama-mcp](https://github.com/mbk-dev/okama-mcp) — MCP server providing investment analysis tools backed by the okama library
- [okama.io](https://okama.io) — live instance of the widgets

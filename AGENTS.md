# AGENTS.md — okama-dash

## Project structure

```
okama-dash/
├── app.py                   # Dash app entry point (dev server, port 8050)
├── run_gunicorn.py          # Production WSGI entry point (imports app.server)
├── navigation.py            # Top navigation bar component
├── footer.py                # Footer component
├── clear_redis_cache.py     # Redis cache flush utility
├── pyproject.toml           # Poetry config, ruff/black settings, dependencies
├── requirements.txt         # Pip fallback (keep in sync with pyproject.toml)
├── .python-version          # Python 3.14
│
├── pages/                   # Multi-page Dash widgets (dash.register_page)
│   ├── efficient_frontier/  # "/" — portfolio optimization, EF chart, transition map
│   ├── compare/             # "/compare" — historical asset performance comparison
│   ├── benchmark/           # "/benchmark" — performance vs benchmark index
│   ├── portfolio/           # "/portfolio" — portfolio analysis, rebalancing, cashflows
│   └── database/            # "/database" — search financial DB (stocks, ETFs, currencies)
│
├── common/                  # Shared modules used across pages
│   ├── settings.py          # App-wide constants (max tickers, MC limits, defaults)
│   ├── symbols.py           # Asset symbol utilities
│   ├── validators.py        # Input validation
│   ├── parse_query.py       # URL query string parsing
│   ├── create_link.py       # Shareable link generation
│   ├── date_input.py        # Date picker components
│   ├── chart_helpers.py     # Plotly helpers (inflation traces, crisis shading, alerts)
│   ├── mantine.py           # Dash Mantine component wrappers
│   ├── update_style.py      # Dynamic style manipulation
│   ├── mobile_screens.py    # Responsive layout adapters
│   ├── object_cache.py      # Unified file-based pickle cache for okama objects
│   ├── math.py              # Financial calculations
│   ├── inflation.py         # Inflation data helpers
│   ├── xlsx.py              # Excel export utilities
│   ├── crisis/              # Crisis period data (shaded chart regions)
│   └── html_elements/       # Custom HTML/Dash components (copy-link, info tables)
│
├── assets/                  # Static files served by Dash (CSS, JS, images)
├── cache-directory/         # Runtime file-system cache (Flask-Caching fallback)
├── tmp/                     # Scratch space for temporary files (contents gitignored)
└── docs/                    # Specs and plans (not deployed)
```

Each page follows the pattern: `pages/<name>/<name>.py` (layout + callbacks) with a
`cards_<name>/` subfolder for card components and `eng/` for English description text.

**Stack:** Dash + Flask, Plotly charts, okama library (financial data & analytics),
Flask-Caching + Redis, Dash Bootstrap + Dash Mantine, Gunicorn (production).

## Running locally

```bash
poetry install
poetry run python app.py          # http://localhost:8050, debug=True (hot reload)
```

**Environment variables** (all optional, with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `OKAMA_CACHE_BACKEND` | `redis` | Cache backend: `redis` or `filesystem` |
| `OKAMA_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (only when backend is `redis`) |

When `OKAMA_CACHE_BACKEND=filesystem`, caching falls back to `cache-directory/` — no Redis needed.

## Deployment

Production deployment on **secondvds** via systemd unit `okama-dash.service`,
running Gunicorn (`run_gunicorn.py`). See project memory for paths and recovery commands.

## Environment & dependencies

- Poetry for environment & dependency management.
- Virtualenv lives at `.venv/` inside the project root (`virtualenvs.in-project = true`).
  When recreating, always run `poetry config virtualenvs.in-project true` before `poetry env use`.
- Always use `poetry add` instead of `pip install`.
- Use `poetry run python ...` to run scripts.
- New dependencies must be added in `pyproject.toml` **and** `requirements.txt`
  (the latter is a top-level-only fallback for non-Poetry environments).

## Test-Driven Development (TDD)

Any change to production code (new feature, bugfix, refactor, behavior change) must follow
TDD: **write a failing test first, then the minimal code that makes it pass**. This overrides
the default "write code, then tests" workflow.

The required workflow is the `superpowers:test-driven-development` skill.
Cycle: **RED → verify RED → GREEN → verify GREEN → REFACTOR**.

Rules for this repo:
- Tests run via: `poetry run pytest -q`.
- Before writing code, see the test fail for a real reason (`AssertionError` / missing function),
  not a typo/import error.
- For bugfix: first a test reproducing the bug, then the fix. Without a reproducing test
  the bug is not considered fixed.
- One test = one behavior. Test name describes the behavior meaningfully, no `test1` / `test_works`.
- Real code instead of mocks wherever possible.
- After GREEN, run the full test suite of the file/module to make sure nothing broke;
  output must be clean (no warnings/errors).
- Exceptions where TDD can be skipped: only by explicit user request (one-time data migration
  scripts, generated code, throwaway prototypes). Notebooks — partial exception: cover the
  library code with tests, not the notebook rendering itself.

## Test suite

278 tests, three-level pyramid (unit → component → E2E). All tests mock okama —
no external API calls, no Redis needed, fully reproducible.

### Structure

```
tests/
├── conftest.py              # Shared fixtures: mock_okama_symbols, mock_portfolio, null_cache
├── mocks/okama_mock.py      # Picklable + MagicMock mocks for Portfolio, AssetList, symbols
├── fixtures/symbols_data.json
├── unit/                    # @pytest.mark.unit — pure logic, no Dash
│   ├── test_validators.py           # validate_integer bounds, types, error messages
│   ├── test_math.py                 # round_list sum preservation
│   ├── test_create_link.py          # URL builder, filename builder, list size check
│   ├── test_symbols.py              # symbol search (prefix, name-token, case-insensitive)
│   ├── test_symbols_cache_isolation.py  # mocked (TESTING) symbol index must not poison real cache (4 tests)
│   ├── test_object_cache.py         # object cache: key building, get_or_create, cleanup (16 tests)
│   └── test_ef_grid.py              # adaptive grid step: predicted points, resolve (Auto), options, parse (7 tests)
├── component/               # @pytest.mark.component — Dash callbacks with mocked okama
│   ├── conftest.py                  # session-scoped Dash app + patched_okama_portfolio
│   ├── test_portfolio_callbacks.py  # pie chart, deviation toggle, cashflow strategies (6 types),
│   │                                # _resolve_indexation, survival stats visibility,
│   │                                # CWD threshold validation, disable Add button logic
│   ├── test_ef_callbacks.py         # normalize_plot_types, resolve_return_column,
│   │                                # portfolio_weights, expand_weights, show/hide callbacks
│   ├── test_ef_click_find.py        # display_click_data (5 tests), find_portfolio (8 tests)
│   ├── test_database_callbacks.py   # db_search (6 tests): search results, empty, namespace routing
│   ├── test_compare_data_callback.py  # update_graf_compare (7): wealth/cumulative_return/cagr/correlation, stats, errors
│   ├── test_benchmark_data_callback.py  # update_graf_benchmark (10): 6 plot types, bar chart, errors
│   ├── test_ef_data_callback.py       # update_ef_cards (8): figures, ef_points×100, mobile, errors, grid trace, grid/MC mode resolution
│   ├── test_ef_grid_callbacks.py     # sim-mode visibility, dynamic grid step options, grid↔pairwise exclusivity, submit gating (6 tests)
│   ├── test_portfolio_data_callback.py  # _update_graf_portfolio_inner (8): figure, y-titles, weights, errors
│   └── test_compare_benchmark_callbacks.py  # change_style_for_hidden_row, show/hide,
│                                            # get_y_title (6 plot types)
└── e2e/                     # @pytest.mark.e2e — Playwright browser tests (Chromium)
    ├── conftest.py                  # Gunicorn server (TESTING=1, 2 workers) + Playwright
    ├── test_portfolio_page.py       # page load (5 controls), navigation (5 pages),
    │                                # mobile viewport 375px (Portfolio + EF)
    ├── test_shareable_links.py      # shareable links: tickers + dates for all 4 pages
    └── test_submit_interaction.py   # Submit → chart with real traces for all 4 pages
```

### Run commands

| Command | Scope | Tests | Duration |
|---------|-------|-------|----------|
| `poetry run pytest -m unit` | Pure logic | 106 | ~4s |
| `poetry run pytest -m component` | Dash callbacks | 152 | ~5s |
| `poetry run pytest -m e2e` | Playwright browser | 20 | ~70s |
| `poetry run pytest -q` | Everything | 278 | ~80s |
| `poetry run pytest -m "not e2e"` | Fast suite | 258 | ~6s |

### What's covered per page

| Page | Unit | Component | E2E |
|------|------|-----------|-----|
| **Portfolio** | create_link, symbols | callbacks (pie chart, cashflow×6, rebalancing, stats), update_graf_portfolio | load, controls, mobile, shareable link, submit→traces |
| **Efficient Frontier** | adaptive grid step (ef_grid) | helpers (normalize, resolve, weights, expand), show/hide, display_click_data, find_portfolio, update_ef_cards, simulation mode (visibility, grid step options, grid↔pairwise exclusivity, submit gating), grid trace | load, mobile, shareable link, submit→chart |
| **Compare** | — | show/hide, update_graf_compare (wealth/cumulative_return/cagr/correlation, stats) | load, shareable link, submit→traces |
| **Benchmark** | — | show/hide, get_y_title, update_graf_benchmark (6 plot types) | load, shareable link, submit→traces |
| **Database** | — | db_search (results, empty, namespace routing, ticker drop) | load |
| **common/** | validators, math, create_link, symbols, object_cache | change_style_for_hidden_row | — |

### okama mock strategy

All tests are independent from external data. okama API is mocked at two levels:

- **Unit/component tests:** `mock_okama_symbols` fixture patches `okama.assets_namespaces`
  and `okama.symbols_in_namespace`. `null_cache` fixture initializes Flask-Caching with
  `NullCache` via `common.cache.init_app()` (the original cache object must be reused because
  `@cache.memoize()` binds at import time). `patched_okama_portfolio` patches `ok.Portfolio`,
  `ok.Rebalance`, and cashflow strategy classes.
- **E2E tests:** `TESTING=1` env var activates mock injection in `app.py` before Dash loads
  pages. Uses **picklable** mock classes (`PicklablePortfolio`, `PicklableAssetList`) instead
  of MagicMock — callbacks can pickle/unpickle portfolio objects and render real chart traces.
  Component tests still use MagicMock factories (`make_mock_portfolio`, `make_mock_asset_list`)
  since they don't go through pickle.

### Adding new tests

- Component tests that import `pages/` modules need the session-scoped `_dash_app` fixture
  from `tests/component/conftest.py` (because `portfolio_controls.py` calls `dash.get_app()`
  at module level).
- E2E server runs via Gunicorn (2 workers) instead of the single-threaded Werkzeug dev
  server, which stalls after ~13 navigations per session.
- E2E tests use `domcontentloaded` wait strategy (not `networkidle`).
- Fixture data lives in `tests/fixtures/symbols_data.json` — 8 mock tickers across 2
  namespaces (US, INDX). Extend this file when new tests need additional symbols.

## Code change workflow

After any code changes, follow this checklist:

1. Determine whether *executable Python code* was changed, not just comments or docstrings.
2. If executable code was changed — always run tests: `poetry run pytest -q`.
3. If only comments, docstrings, or Jupyter Notebook files were changed — do not run tests.
4. If tests reveal failures, attempt to fix and re-run (max 2 retries).
   If still failing, stop and report the remaining issues.
5. Before finishing any code change (including notebooks), run `poetry run ruff check .`
   and fix every reported issue. If a warning is truly unavoidable, silence it with a
   targeted `# noqa: <CODE>` comment on the offending line and include a brief rationale.
   Never disable rules globally or use a bare `# noqa`.
6. After finishing a batch of changes, verify that `AGENTS.md` (test counts, structure
   tree, coverage table, gaps section) and project memory are still accurate. Update any
   stale numbers, descriptions, or file listings before committing.

## Recording findings in memory

Whenever you incidentally discover something worth fixing that is **out of scope
for the current task** — a bug, a factual inaccuracy in code/docs, code that can
be improved (dead code, deprecations, smells), or a security issue — record it in
project memory yourself instead of silently moving on. Do not wait to be asked.

- Append it to the `findings-to-fix` memory (running log of open findings), with a
  short description, the date you noticed it, affected files, and a suggested fix.
- Add or update the one-line pointer in `MEMORY.md`.
- If the finding is in scope for the task you're already doing, just fix it (per
  the TDD and code-change rules) — the log is only for things you won't fix now.
- When a logged finding is later fixed, strike it through with the date rather than
  deleting it, so the history stays visible.

This keeps mid-task discoveries from being lost and gives one place to look before
planning cleanup or refactor work.

## Temporary files

- Any temporary or throwaway file (scratch scripts, screenshots from manual
  verification, ad-hoc data dumps, intermediate exports) must be created inside
  the `tmp/` directory at the project root — never in the project root itself or
  in source/test folders.
- Delete each temporary file as soon as it is no longer needed. Do not leave
  scratch artifacts behind after a task is finished.
- `tmp/` is tracked (via `tmp/.gitignore`) but its contents are ignored, so
  nothing written there can be committed by accident.

## Python style & modernization

- Write new code with modern syntax and avoid legacy forms:
  - Use built-in generics: `list[int]`, `dict[str, Any]`, `tuple[int, ...]`
    instead of `typing.List` / `Dict` / `Tuple`.
  - Use union syntax `X | Y` and `X | None` instead of `typing.Union` / `typing.Optional`.
  - Prefer literals over constructor calls: `{}`, `[]`, `set()` — avoid `dict()`, `list()`
    when a literal works. In particular, never write `dict()` for an empty dict,
    and never wrap `kwargs`-style pairs as `dict(a=1, b=2)` when a literal is clearer.
  - Use `dict(zip(a, b))` instead of `{k: v for k, v in zip(a, b)}` (ruff C416).
  - Use set literals `{"a", "b"}` instead of `set(["a", "b"])` (ruff C405).
  - Never use mutable default arguments (`def f(x=[])` / `x={}`). Use `None` and
    initialize inside the function body (ruff B006). For simple fixed pairs like
    `figsize=(12, 6)`, prefer a tuple.
  - Keep `matplotlib` `bbox=` / style kwargs as dict literals, not `dict(...)` calls.
- **Ruff configuration** is in `pyproject.toml` (`[tool.ruff.lint]`, selecting `C,E,F,W,B`).
  Treat it as the authoritative style guide — if ruff is silent, the style is acceptable.

## Code conventions

- Always write all code comments, docstrings, and documentation in **English**, even if the
  task description or existing code is in another language (e.g. Russian).
- Use type hints for all function parameters and return types.
- Use f-string formatting for all logging and print messages.
- When editing Jupyter Notebook examples in the `/examples` directory, ensure that the code
  examples are up-to-date with the current codebase in the Git branch.

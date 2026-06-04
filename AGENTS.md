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

347 tests, three-level pyramid (unit → component → E2E). All tests mock okama —
no external API calls, no Redis needed, fully reproducible.

### Structure

```
tests/
├── conftest.py              # Shared fixtures: mock_okama_symbols, mock_portfolio, null_cache
├── mocks/okama_mock.py      # Picklable + MagicMock mocks for Portfolio, AssetList, symbols
├── fixtures/symbols_data.json
├── unit/                    # @pytest.mark.unit — pure logic, no Dash
│   ├── conftest.py                  # session-scoped Dash app (for unit tests importing pages/ modules)
│   ├── test_validators.py           # validate_integer bounds, types, error messages
│   ├── test_math.py                 # round_list sum preservation
│   ├── test_create_link.py          # URL builder, filename builder, list size check
│   ├── test_symbols.py              # symbol search (prefix, name-token, case-insensitive)
│   ├── test_symbols_cache_isolation.py  # mocked (TESTING) symbol index must not poison real cache (4 tests)
│   ├── test_object_cache.py         # object cache: key building, get_or_create, cleanup, filename-length guard (22 tests)
│   ├── test_ef_grid.py              # adaptive grid step: predicted points, resolve (Auto), options, parse (7 tests)
│   ├── test_chart_helpers.py        # add_return_type_annotation: CAGR note, default, no-arrow (3 tests)
│   └── test_mc_distribution_parameters.py  # build_distribution_parameters: norm/lognorm/t mapping, empty→None, lognorm loc=-1; reactive-estimation gates: _portfolio_is_complete (sum=100, tolerance), _valid_mc_date (17 tests)
├── component/               # @pytest.mark.component — Dash callbacks with mocked okama
│   ├── conftest.py                  # session-scoped Dash app + patched_okama_portfolio
│   ├── test_portfolio_callbacks.py  # pie chart, deviation toggle, cashflow strategies (6 types),
│   │                                # _resolve_indexation + _resolve_discount_rate (percent ÷100),
│   │                                # survival stats visibility,
│   │                                # CWD threshold validation, disable Add button logic,
│   │                                # percentage input lives in cash-flow frequency row
│   ├── test_ef_callbacks.py         # normalize_plot_types, resolve_return_column,
│   │                                # portfolio_weights, expand_weights, show/hide callbacks
│   ├── test_ef_click_find.py        # display_click_data (5 tests), find_portfolio (8 tests)
│   ├── test_database_callbacks.py   # db_search (6 tests): search results, empty, namespace routing
│   ├── test_compare_data_callback.py  # update_graf_compare (9): wealth/cumulative_return/annual_return(bar, CAGR annotation)/cagr/correlation, stats, errors
│   ├── test_benchmark_data_callback.py  # update_graf_benchmark (10): 6 plot types, bar chart, errors
│   ├── test_ef_data_callback.py       # update_ef_cards (8): figures, ef_points×100, mobile, errors, grid trace, grid/MC mode resolution
│   ├── test_ef_grid_callbacks.py     # sim-mode visibility, dynamic grid step options, grid↔pairwise exclusivity, submit gating (6 tests)
│   ├── test_portfolio_data_callback.py  # _update_graf_portfolio_inner (11): figure, y-titles (incl. annual_return), weights, discount-rate wiring to dcf (÷100), errors; get_pf_figure annual_return bar chart (2: bars + CAGR return_type/annotation); update_graf_portfolio outer (toast, arity); show_graf_and_statistics_rows (reveal on submit)
│   ├── test_mc_params_callbacks.py   # MC distribution parameters: set_mc_parameters wiring, submit tuple build, show_hide_param_groups, collapse toggle, hide_monte_carlo_rows (6 rows), reactive auto_estimate_distribution_parameters (gates, norm/lognorm/t fit, VaR-level df optimize + reset-on-clear, errors), df>2 validation (23 tests)
│   └── test_compare_benchmark_callbacks.py  # change_style_for_hidden_row, show/hide,
│                                            # get_y_title (6 plot types), rolling-window disabled for annual_return (compare + portfolio)
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
| `poetry run pytest -m unit` | Pure logic | 132 | ~4s |
| `poetry run pytest -m component` | Dash callbacks | 195 | ~5s |
| `poetry run pytest -m e2e` | Playwright browser | 20 | ~70s |
| `poetry run pytest -q` | Everything | 347 | ~80s |
| `poetry run pytest -m "not e2e"` | Fast suite | 327 | ~6s |

### What's covered per page

| Page | Unit | Component | E2E |
|------|------|-----------|-----|
| **Portfolio** | create_link, symbols, build_distribution_parameters, reactive-estimation gates | callbacks (pie chart, cashflow×6, rebalancing, stats), update_graf_portfolio, annual_return bar chart, rolling-window gating, percent rate inputs (discount/indexation ÷100), discount-rate wiring to dcf, MC distribution parameters (groups show/hide, collapse toggle, reactive background estimation + VaR-level df optimization, df>2 validation, set_mc_parameters wiring) | load, controls, mobile, shareable link, submit→traces |
| **Efficient Frontier** | adaptive grid step (ef_grid) | helpers (normalize, resolve, weights, expand), show/hide, display_click_data, find_portfolio, update_ef_cards, simulation mode (visibility, grid step options, grid↔pairwise exclusivity, submit gating), grid trace | load, mobile, shareable link, submit→chart |
| **Compare** | — | show/hide, update_graf_compare (wealth/cumulative_return/annual_return bar/cagr/correlation, stats), rolling-window gating | load, shareable link, submit→traces |
| **Benchmark** | — | show/hide, get_y_title, update_graf_benchmark (6 plot types) | load, shareable link, submit→traces |
| **Database** | — | db_search (results, empty, namespace routing, ticker drop) | load |
| **common/** | validators, math, create_link, symbols, object_cache, chart_helpers (add_return_type_annotation) | change_style_for_hidden_row | — |

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
- Fixture data lives in `tests/fixtures/symbols_data.json` — 7 mock tickers across 2
  namespaces (US, INDX), all verified to resolve in the real okama database. Extend this
  file when new tests need additional symbols.

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

## Ticker symbols — verify against the database, never invent

Every ticker symbol you use must be a **real, verified okama database symbol**. Do not
make up plausible-looking tickers from memory or pattern-matching (e.g. assuming the S&P 500
index is `SP500.INDX`). This is a concrete instance of the global "don't speculate" rule.

- **Verify before use.** Confirm a symbol exists with `ok.Asset("<SYMBOL>")` (raises a 404
  `HTTPError` if absent) or by scanning `ok.symbols_in_namespace("<NS>")`. Do this whenever you
  introduce a symbol — in tests, fixtures, example notebooks, shareable-link defaults, or a
  manual/local check.
- **Especially in tests and fixtures.** The unit/component mocks accept any string, so an
  invented ticker passes there silently — but e2e tests, any real-okama code path, and manual
  page captures hit the **real** database and 404. Keep `tests/fixtures/symbols_data.json` (and
  any other hard-coded symbols) limited to symbols that actually resolve in okama, so the mock
  mirrors reality.
- **Known pitfall.** `SP500.INDX` *looks* valid but 404s in the real okama DB; the S&P 500
  total-return index is `SP500TR.INDX`. Verified safe examples: `AAPL.US`, `MSFT.US`, `GOOG.US`,
  `SPY.US` (S&P 500 ETF), `SP500TR.INDX`, `MCFTR.INDX`.

## UI layout & form design conventions

Form controls across the widgets must stay visually consistent. The rules below
are enforced globally in `assets/forms.css` (Dash auto-serves any CSS in `assets/`),
so prefer fixing the shared stylesheet/convention over per-component patches.

- **Equal height in a row.** Every interactive control is **38px** tall. `dbc.Input`/
  `dbc.Select` are 38px by default; `dcc.Dropdown` (34px) and `dmc.Select` (36px) are
  normalized up to 38px in `assets/forms.css`. When you place a dropdown/select next to
  an input in the same `dbc.Row`, you don't need extra styling — they already line up.
- **Vertical rhythm — rows never touch.** A container that stacks form rows must own the
  vertical gap, not the rows. Use Bootstrap's **`vstack gap-2`** (0.5rem) on the container
  (`html.Div(..., className="vstack gap-2")`), or `class_name="mb-2"` on each row. This
  guarantees a consistent gap even for rows added dynamically. The wrapper owns the rhythm
  at *every* level — e.g. the Tickers/Weights block applies `vstack gap-2` both to the inner
  `#dynamic-container` (asset rows) **and** to the outer block `Div` so the header and the
  "Add Asset" button get the same gap. Reference implementation:
  `pages/portfolio/cards_portfolio/portfolio_controls.py`.
- **Buttons never sit flush against the control above them.** Two button roles:
  - *Primary action* (Submit / Compare / Search / Find portfolio / Backtest): centered and
    wrapped in `html.Div([button], className="p-3", style={"text-align": "center"})` for
    breathing room. This is the existing convention on every page except where noted — keep it.
  - *Inline / list action* (Add Asset / Add Entry / Add Threshold): left-aligned inside its
    form block and spaced by the block's vertical rhythm (`vstack gap-2`, or `mt-2` on its
    row) — at minimum a `0.5rem` gap, never `0`.
- **Tooltips describe the financial parameter, not the front-end mechanics.** A control's
  tooltip explains what the parameter means financially (what it measures, its units, how it
  affects the calculation) — not when or how the UI fills, recomputes, enables, disables or
  hides it. Keep tooltips short. Example: "VaR confidence level (1-99) at which the degrees
  of freedom (df) of Student's t-distribution are optimized..." — good; "Enter a value to
  recompute the field; clear it to reset..." — bad.
- These are visual/markup changes — verify by eye on the live local site (see below), no
  unit test per the TDD-skip rule for non-logic changes.

### Live local review before committing (visual/design tasks)

When a task touches **visual design elements** (layout, CSS, markup, component styling,
spacing, ordering, wrappers — anything whose effect is *seen* rather than computed), the
user reviews the result on the running site **before** it is committed. Before reporting
such work as done:

- **Check whether the local dev server is running** (default `http://localhost:8050`). If
  it is not up, start it (`poetry run python app.py`, debug=True) so the user can open the
  page and see the change live.
- **Point the user to where to look** — the route/page and which control or panel changed —
  so they can review it on the live site.
- **Don't commit a visual change until the user has had the chance to see it live** (commit
  only when they ask, per the Git push policy below).
- **No screenshots by default.** Do not capture or attach screenshots unless the user
  explicitly asks for them — the live local site is the review surface, not an image.

## Git push policy (OpenClaw-агенты)

Действует совместно с глобальным правилом `claw_agent_git_push`. Агент на claw
коммитит и пушит автономно ТОЛЬКО в work/test-ветки; в прод-ветку — только после
явного подтверждения пользователя в Matrix.

- **Work/test (автономно):** `dev`, feature-ветки
- **Прод (только с подтверждением):** `master` (default/release)

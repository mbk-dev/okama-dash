# AGENTS.md — okama-dash

## Project structure

```
okama-dash/
├── app.py                   # Dash app entry point (dev server, port 8050)
├── run_gunicorn.py          # Production WSGI entry point (imports app.server)
├── navigation.py            # Top navigation bar component
├── footer.py                # Footer component
├── clear_redis_cache.py     # Redis cache flush utility
├── pyproject.toml           # Poetry config, ruff settings, dependencies
├── requirements.txt         # Pip fallback (keep in sync with pyproject.toml)
├── .python-version          # Python 3.14
│
├── pages/                   # Multi-page Dash widgets (dash.register_page)
│   ├── efficient_frontier/  # "/" — portfolio optimization, EF chart, transition map
│   ├── compare/             # "/compare" — historical asset performance comparison
│   ├── benchmark/           # "/benchmark" — performance vs benchmark index
│   ├── portfolio/           # "/portfolio" — portfolio analysis, rebalancing, cashflows
│   ├── database/            # "/database" — search financial DB (stocks, ETFs, currencies)
│   └── macro/               # "/macro/*" — macro indicators: inflation, rates (key rates), CAPE10, real estate
│
├── common/                  # Shared modules used across pages
│   ├── settings.py          # App-wide constants (max tickers, MC limits, defaults)
│   ├── symbols.py           # Asset symbol utilities
│   ├── validators.py        # Input validation
│   ├── parse_query.py       # URL query string parsing
│   ├── create_link.py       # Shareable link generation (incl. pf_* portfolio handoff group)
│   ├── url_portfolio.py     # pf_* URL portfolio handoff: parse group, chip split, cached ok.Portfolio (Compare/Benchmark)
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
│   └── html_elements/       # Custom HTML/Dash components (copy-link, info tables, grid export, submit spinner)
│
├── tools/                   # Dev-only scripts, not deployed (dump_callbacks.py — greppable callback wiring map; bench_server.py — server load/timing benchmark, see .claude/skills/test_server_load)
├── assets/                  # Static files served by Dash (CSS, JS, images; dashAgGridFunctions.js — AG Grid formatter functions; charts.css — full-bleed mobile chart cards; grids.css — compact wrapText line-height in AG Grid cells; chart_yrescale.js — global plotly_relayout listener that auto-rescales the Y axis to the visible X window when the range slider zooms, shared across every chart, #26; select_tab_complete.js — global keydown listener: Tab on an open searchable dmc.Select/MultiSelect picks the top match; MultiSelect (multi-ticker) keeps the cursor in the search box for the next ticker, single Select moves focus on; shared across every ticker selector, #25)
├── cache-directory/         # Runtime file-system cache (Flask-Caching fallback)
├── tmp/                     # Scratch space for temporary files (contents gitignored)
├── docs/                    # Specs and plans (not deployed)
└── .rgignore                # ripgrep: default searches skip tests/ (see "Searching the codebase")
```

Each page follows the pattern: `pages/<name>/<name>.py` (layout + callbacks) with a
`cards_<name>/` subfolder for card components and `eng/` for English description text.

**Stack:** Dash + Flask, Plotly charts, Dash AG Grid, okama library (financial data & analytics),
Flask-Caching + Redis, Dash Bootstrap + Dash Mantine, Gunicorn (production).

## Searching the codebase

Tests are ~40% of the repo's Python and mirror production terms, so untargeted greps
drown in test hits. Conventions:

- **`.rgignore` excludes `tests/` from default ripgrep traversal** (and from Claude Code's
  Grep tool, which is ripgrep-based). A repo-wide `rg <pattern>` returns production code only.
- **Explicit paths bypass the ignore** — `rg <pattern> tests/` or naming a test file works
  with no extra flags (verified behavior; `--no-ignore` is never needed for explicit paths).
- **Usage searches before a refactor MUST include tests.** When renaming/moving any function,
  id, or fixture, search both: `rg <pattern>` *and* `rg <pattern> tests/` — otherwise test
  usages are silently missed and the suite breaks. This is the deliberate trade-off of the
  `.rgignore` default.
- **Callback wiring questions go through the callback map, not grep.** Dash wires callbacks
  by string component ids, invisible to symbol tools (LSP/code graphs — evaluated and
  rejected; see project memory). Dash keeps the registry itself, so dump it:

  ```bash
  poetry run python tools/dump_callbacks.py              # full map: file:line, fn, out/in/state
  poetry run python tools/dump_callbacks.py | rg pf-graf # full wiring of one component id
  ```

  One line per callback: `<file>:<line> <function> | out: id.prop | in: id.prop, ... | state: ...`.
  The script imports the app under `TESTING=1` (mocked okama — no network, no Redis writes).

## Running locally

```bash
poetry install
poetry run python app.py          # http://localhost:8050, debug=True (hot reload) — manual dev
```

**Agent-launched local server: Gunicorn on port 8051.** When the agent (Claude) needs
to bring the app up itself — for a live review, a headless check, or a screenshot — it
MUST start it as:

```bash
.venv/bin/gunicorn run_gunicorn:server -b 127.0.0.1:8051 -w 2 --timeout 120
```

launched through the harness's background mechanism (`run_in_background`), with **no**
`TESTING=1` (real okama data). Rationale, all verified on this host:
- **Port 8051, not 8050** — a manual `python app.py` dev server (or one from a parallel
  git worktree) often already holds 8050; sharing it serves a stale build. 8051 keeps the
  agent's server distinct.
- **Gunicorn, not `app.run` in the background** — `python app.py` (werkzeug) dies when
  detached: okama pulls in loky/joblib whose semaphores don't survive a `nohup &`/`setsid`
  detach in this WSL2 environment. A plain `&` also gets reaped when the Bash tool call
  ends. The Gunicorn master under harness background-tracking stays up.
- **No hot reload** — Gunicorn won't pick up edits; restart it after code changes.

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
- Before writing a new test, look for existing tests, fixtures, and mock factories with an
  explicit path — `rg <pattern> tests/` — because the default search skips `tests/` (see
  "Searching the codebase"). An empty default-search result does NOT mean the fixture or
  test doesn't exist.
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

892 tests, three-level pyramid (unit → component → E2E). All tests mock okama —
no external API calls, no Redis needed, fully reproducible. (Known exception:
`ok.EfficientFrontier` is not patched by the TESTING block — see "Known gaps" below.)

### Structure

```
tests/
├── conftest.py              # Shared fixtures: mock_okama_symbols, mock_portfolio, null_cache
├── mocks/okama_mock.py      # Picklable + MagicMock mocks for Portfolio, AssetList, symbols
├── fixtures/symbols_data.json
├── unit/                    # @pytest.mark.unit — pure logic, no Dash
├── component/               # @pytest.mark.component — Dash callbacks with mocked okama
└── e2e/                     # @pytest.mark.e2e — Playwright/Chromium (Gunicorn server, TESTING=1)
```

The exhaustive per-test-file inventory used to live here but was removed: it drifted on every
test change and only restated what the tests already document. **The test files are the source
of truth** — list and read them directly (the default `rg` skips `tests/`, so name the path):

```bash
ls tests/unit tests/component tests/e2e        # what test files exist
rg <behavior-or-id> tests/                     # find the test(s) for a behavior/id (e.g. pf_*, #23)
```

Rough grouping:
- **unit/** — `common/` + `tools/` pure logic: validators, math, create_link, symbols, object_cache,
  ef_grid, chart_helpers, inflation, MC distribution params, find-withdrawal helpers, dump_callbacks,
  and the macro catalog/mocks/objects/stats/link tests.
- **component/** — one `*_callbacks.py` / `*_data_callback.py` per page (portfolio, ef, compare,
  benchmark, database, macro) plus cross-cutting: grid_export, grid_sorting, submit_spinner,
  url_ccy_normalization, mc_params.
- **e2e/** — page load, shareable links, submit→chart, macro reactive render (4 files).

### Run commands

| Command | Scope | Tests | Duration |
|---------|-------|-------|----------|
| `poetry run pytest -m unit` | Pure logic | 300 | ~2s |
| `poetry run pytest -m component` | Dash callbacks | 550 | ~9s |
| `poetry run pytest -m e2e` | Playwright browser | 42 | ~100s |
| `poetry run pytest -q` | Everything | 892 | ~118s |
| `poetry run pytest -m "not e2e"` | Fast suite | 850 | ~10s |

**E2E server output must stay on DEVNULL.** The Gunicorn subprocess in `tests/e2e/conftest.py`
redirects stdout/stderr to `subprocess.DEVNULL` deliberately: with `PIPE` nobody drains the
pipes, so once app logging fills the 64 KiB buffer (~17 navigations, since reactive MC
estimation logs per page load) gunicorn blocks on write and every later request times out
(the 2026-06-04 "5 e2e timeouts" incident). If you need server logs for debugging, redirect
to a file in `tmp/` instead of `PIPE`.

### Known gaps

Blind spots the suite is known not to cover. Check here before trusting a green
run on these areas; strike items out (or remove them) when fixed.

- **EF e2e runs against the real okama API**
  ([#12](https://github.com/mbk-dev/okama-dash/issues/12)): the TESTING block does
  not patch `ok.EfficientFrontier`, and the mocked currency list is empty
  (ccy=None → 404), so the EF submit in e2e renders an error-annotation figure;
  `test_ef_submit_shows_chart` asserts only that an svg exists, which the error
  figure satisfies. EF chart correctness is therefore not e2e-verified. The same
  blind spot covers the URL-portfolio star point: `get_portfolio_point`'s real
  okama accessor arithmetic (`risk_annual.iloc[-1]`, `get_cagr().iloc[-1][symbol]`)
  runs only against mocked shapes in CI; the star's numeric coordinates were
  verified manually against okama 2.2.0 (2026-06-05), not regression-guarded.
- **AG Grid client-side formatters are not executable in tests**: valueFormatter
  functions live as JS strings (`assets/dashAgGridFunctions.js`) parsed in the
  browser. Unit/component tests can only assert the wiring (function name present
  in columnDefs); actual formatting regressions are caught only by e2e DOM
  assertions.
- **Interrupted e2e runs leak Gunicorn masters**: the server teardown in
  `tests/e2e/conftest.py` does not run when pytest is killed mid-session. After an
  aborted e2e run, check `pgrep -f 'gunicorn run_gunicorn'` and kill leftovers.
- **`test_corrupt_file_reconstructs` (test_object_cache.py) flakes under
  concurrent pytest runs** — suspected shared `cache-directory/` contention
  between simultaneous pytest processes. Passes solo and in normal runs.

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
- Fixture data lives in `tests/fixtures/symbols_data.json` — 10 mock symbols across 3
  namespaces (US, INDX, INFL — currencies for ccy validation), all verified to resolve in
  the real okama database. INFL sits in `symbols_by_namespace` only, NOT in the
  `namespaces` list, so the Database page namespace options stay unchanged. Extend this
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
   tree skeleton, gaps section) and project memory are still accurate. Update any
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
  `dbc.Select` are 38px by default; `dcc.Dropdown` (34px), `dmc.Select` and
  `dmc.NumberInput` (36px) are normalized up to 38px in `assets/forms.css`. When you place
  a dropdown/select next to an input in the same `dbc.Row`, you don't need extra styling —
  they already line up.
- **Vertical rhythm — rows never touch.** A container that stacks form rows must own the
  vertical gap, not the rows. Use Bootstrap's **`vstack gap-2`** (0.5rem) on the container
  (`html.Div(..., className="vstack gap-2")`), or `class_name="mb-2"` on each row. This
  guarantees a consistent gap even for rows added dynamically. The wrapper owns the rhythm
  at *every* level — e.g. the Tickers/Weights block applies `vstack gap-2` both to the inner
  `#dynamic-container` (asset rows) **and** to the outer block `Div` so the header and the
  "Add Asset" button get the same gap. Reference implementation:
  `pages/portfolio/cards_portfolio/portfolio_controls.py`.
- **Moving an element changes its neighbors — re-check every gap.** Whenever a button or
  any design element is inserted, moved, or re-parented, verify its spacing against ALL
  adjacent elements (above, below, sides) by eye on the live local site, desktop and
  mobile widths — not just the element's own styling. The trap (produced #20): an element
  that moves into a different container — especially as its first or last child — loses
  the margin it used to inherit from the old markup, and the container boundary lands
  flush against the container's *outside* neighbor. So check the first/last-child
  boundaries of the new container against what sits around it. The "wrapper owns the
  rhythm" rule above says *how* to fix a missing gap; this rule says *when to look*:
  every insertion or move.
- **Buttons never sit flush against the control above them.** Two button roles:
  - *Primary action* (Submit / Compare / Search / Find portfolio / Backtest): centered and
    wrapped in `html.Div([button], className="p-3", style={"textAlign": "center"})` for
    breathing room. This is the existing convention on every page except where noted — keep it.
    Inline `style` dict keys are always camelCase (`textAlign`, not `"text-align"`) — React
    warns on kebab-case keys and only applies them by browser leniency.
  - *Inline / list action* (Add Asset / Add Entry / Add Threshold): left-aligned inside its
    form block and spaced by the block's vertical rhythm (`vstack gap-2`, or `mt-2` on its
    row) — at minimum a `0.5rem` gap, never `0`.
- **Tooltips describe the financial parameter, not the front-end mechanics.** A control's
  tooltip explains what the parameter means financially (what it measures, its units, how it
  affects the calculation) — not when or how the UI fills, recomputes, enables, disables or
  hides it. Keep tooltips short. Example: "VaR confidence level (1-99) at which the degrees
  of freedom (df) of Student's t-distribution are optimized..." — good; "Enter a value to
  recompute the field; clear it to reset..." — bad.
- **Mobile charts are full-bleed.** Below 800px (`screen["in_width"] < 800`, same breakpoint
  in `assets/charts.css`) every Plotly chart sticks to the screen edges: the chart card carries
  the `chart-card` class (negative half-gutter margin, no side padding/borders — `charts.css`),
  and `common/mobile_screens.py::adopt_small_screens` sets zero side margins, y-tick labels
  inside the plot, no y-axis title, and the legend below the chart (container-ref, title on its
  own row). Exception: the Compare correlation matrix keeps tick labels outside (ticker names).
  New chart cards must get `class_name="chart-card mb-3"` and route figures through
  `adopt_small_screens`.
- **Mobile stats tables reflow to one pair per row.** The Portfolio MC Survival/Wealth
  statistics tables keep their two-pane desktop layout only when `is_small_screen(screen)`
  is False; on mobile the builders take `compact=True` and emit a single column of pairs.
  Apply the same pattern to any new multi-pane table.
- **Tables are informational — no column sorting.** Every `dag.AgGrid` sets
  `defaultColDef={"resizable": False, "sortable": False}` (AG Grid columns are sortable
  by default). New grids must follow suit; `tests/component/test_grid_sorting.py` asserts
  the wiring on all existing grid builders.
- **Macro pages are chart-first and fully reactive.** All four `/macro/*` pages use a one-row control bar above the chart (no controls/info card pair, no Submit button) and recalculate on every control change: all controls are Inputs of the main callback, which also omits `prevent_initial_call` so the chart renders on page load. `dates_ready` guards against half-typed YYYY-MM dates reaching okama; an empty series selection keeps the last chart (PreventUpdate) and disables Copy link. The control row is top-aligned (`align="start"`) so all 38px controls share one line while the dates' FormText hangs below. Secondary selectors that repopulate another control (the rates group dropdown) update that control's options+value and are deliberately NOT main-callback Inputs (stale-value double-fire). Every macro chart carries a **Download data** link below it (shared `macro_chart_card` block + `register_macro_download(prefix)`): the main callback emits the plotted dataframe as JSON into `{prefix}-store-chart-data`, the button converts it to xlsx via `common/xlsx.py::json_to_download_xlsx_object` — so each figure builder returns `(figure, dataframe)`.
- These are visual/markup changes — verify by eye on the live local site (see below), no
  unit test per the TDD-skip rule for non-logic changes.

### Live local review before committing (visual/design tasks)

When a task touches **visual design elements** (layout, CSS, markup, component styling,
spacing, ordering, wrappers — anything whose effect is *seen* rather than computed), the
user reviews the result on the running site **before** it is committed. Before reporting
such work as done:

- **Check whether the local dev server is running.** If the user runs it themselves it is
  `http://localhost:8050` (`poetry run python app.py`). When the agent brings it up, use the
  Gunicorn-on-8051 recipe from "Running locally" above (`http://localhost:8051`) — don't try
  to background `app.py`. Either way, point the user at the running URL.
- **Point the user to where to look** — the route/page and which control or panel changed —
  so they can review it on the live site.
- **Don't commit a visual change until the user has had the chance to see it live** (commit
  only when they ask, per the Git push policy below).
- **No screenshots by default.** Do not capture or attach screenshots unless the user
  explicitly asks for them — the live local site is the review surface, not an image.

## Layout decomposition (no monolithic layouts)

A layout — a builder function, or a card/page module pairing a layout with its callbacks —
must not grow into one giant blob. Split it by **feature** into a package: a thin `layout.py`
assembler plus one submodule per feature (its sub-layout + callbacks + helpers together, high
cohesion), with `__init__.py` re-exporting the public names so every existing import and every
callback wiring (by string id) keeps working unchanged. Signal to split: a builder function over
~150–200 lines, or a module mixing a large layout with many callbacks (guideline, use judgement).
It is a behavior-preserving refactor — carve sections verbatim, change only imports — so it needs
no new test; the existing suite (+ `poetry run python tools/dump_callbacks.py`) is the safety net.

**Full procedure → the `split_large_layout` skill** (mapping the import surface incl. `tests/`,
verbatim-carve pitfalls, `__init__` re-exports, the `dump_callbacks` + e2e verification gates).
Reference: `pages/portfolio/cards_portfolio/cashflow_controls/` (a 1265-line file split into
constants / helpers / common / vds / cwd / find / timeseries / layout).

## Release gate (master)

Before ANY release to `master` (merging `dev`/a feature branch into `master`, or
pushing release commits to it), the FULL test suite must pass: `poetry run pytest -q`
— all tests including e2e. The fast subset (`-m "not e2e"`) is NOT sufficient for a
release. This applies to every actor (user, laptop Claude, OpenClaw agents) and
complements the per-change checklist in "Code change workflow".

## Git push policy (OpenClaw-агенты)

Действует совместно с глобальным правилом `claw_agent_git_push`. Агент на claw
коммитит и пушит автономно ТОЛЬКО в work/test-ветки; в прод-ветку — только после
явного подтверждения пользователя в Matrix.

- **Work/test (автономно):** `dev`, feature-ветки
- **Прод (только с подтверждением):** `master` (default/release)

## Создание веток и worktree — только по команде пользователя

Новая git-ветка и новый git worktree создаются **только по явной команде
пользователя или с его разрешения**. Не создавай их по собственной инициативе —
даже чтобы «изолировать» задачу, начать работу над фичей или выполнить план. Если
кажется, что задаче нужна отдельная ветка/worktree, **сначала спроси** и дождись
согласия; по умолчанию работай в текущей ветке и директории.

Это **переопределяет** дефолт скилла `superpowers:using-git-worktrees` (который иначе
создаёт worktree автоматически): в этом проекте такой шаг требует подтверждения
(приоритет инструкций пользователя над скиллами).

## Worktree — уборка после мерджа в dev

Когда ветка задачи смерджена в `dev`, её worktree удаляется вместе с директорией
(`git worktree remove <path>`, запуск из другой директории — не изнутри worktree; не `rm -rf`)
— не оставляй отработавшие worktree висеть.

**Критично: сначала спаси проектную память worktree, потом удаляй.** Worktree пишет память в
свой namespace (`~/.claude/projects/-home-…-okama-dash-<task>/memory/`) — отдельную, **не**
синкаемую директорию, которой нет в `~/claude`. При удалении worktree она теряется. Перед
`git worktree remove` перенеси новые/обновлённые файлы в синкаемую `~/claude/memory/okama-dash/`
(не затирая более свежие), обнови `MEMORY.md`, закоммить+запушь `~/claude`.

**Полный workflow → скилл `cleanup_worktree`** (точные пути namespace, перенос памяти, почему
`git worktree remove` (а не `rm -rf`), запуск из другой директории, удаление ветки).

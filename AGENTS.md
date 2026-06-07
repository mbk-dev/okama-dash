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
│   └── macro/               # "/macro/*" — macro indicators: inflation, key rates, CAPE10 (stage 1)
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
│   └── html_elements/       # Custom HTML/Dash components (copy-link, info tables, grid export, submit spinner)
│
├── tools/                   # Dev-only scripts, not deployed (dump_callbacks.py — greppable callback wiring map; bench_server.py — server load/timing benchmark, see .claude/skills/test_server_load)
├── assets/                  # Static files served by Dash (CSS, JS, images; dashAgGridFunctions.js — AG Grid formatter functions; charts.css — full-bleed mobile chart cards; grids.css — compact wrapText line-height in AG Grid cells)
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

707 tests, three-level pyramid (unit → component → E2E). All tests mock okama —
no external API calls, no Redis needed, fully reproducible. (Known exception:
`ok.EfficientFrontier` is not patched by the TESTING block — see "Known gaps" below.)

### Structure

```
tests/
├── conftest.py              # Shared fixtures: mock_okama_symbols, mock_portfolio, null_cache
├── mocks/okama_mock.py      # Picklable + MagicMock mocks for Portfolio, AssetList, symbols
├── fixtures/symbols_data.json
├── unit/                    # @pytest.mark.unit — pure logic, no Dash
│   ├── conftest.py                  # session-scoped Dash app (for unit tests importing pages/ modules)
│   ├── test_validators.py           # validate_integer bounds, types, error messages; validate_integer_bool (21 tests)
│   ├── test_math.py                 # round_list rounding & sum preservation (8 tests)
│   ├── test_create_link.py          # URL builder, filename builder, list size check; param grouping (base→identity→rebal→cashflow); inactive-strategy params omitted; scope_cashflow_params; cf_ts owned by every strategy + zero-primary-with-cf_ts counts as active; "" (cleared dmc.NumberInput) treated as unset by skip_if_default. NOTE: MC params are deliberately NOT in shareable links — none are emitted/parsed (74 tests)
│   ├── test_symbols.py              # symbol lists, search index, search (prefix, name-token, case-insensitive) (23 tests)
│   ├── test_symbols_cache_isolation.py  # mocked (TESTING) symbol index must not poison real cache (4 tests)
│   ├── test_object_cache.py         # object cache: key building, get_or_create, cleanup, filename-length guard; TESTING flag isolation (env poisoning guard) (25 tests)
│   ├── test_ef_grid.py              # adaptive grid step: predicted points, resolve (Auto), options, parse (7 tests)
│   ├── test_ef_label_padding.py     # EF x-range label padding: centered labels reserve half width on both sides (2 tests)
│   ├── test_chart_helpers.py        # add_return_type_subtitle: CAGR note, default, left-aligned title; format_points (integer points, space thousands separator) (6 tests)
│   ├── test_inflation.py            # resolve_url_currency (case-insensitive, validated, page-default fallback); currency list memoized 30 days with TESTING-token cache isolation (9 tests)
│   ├── test_mc_distribution_parameters.py  # build_distribution_parameters: norm/lognorm/t mapping, empty→None, lognorm loc=-1; reactive-estimation gates: _portfolio_is_complete (sum=100, tolerance), _valid_mc_date (18 tests)
│   ├── test_ef_portfolio_card.py    # EF portfolio card builder: stat blocks, title/badge, allocation rows with percent + stacked bar (plotly palette colors, zero-weight segments skipped), None-weights note (9 tests)
│   ├── test_dump_callbacks.py       # tools/dump_callbacks formatter: file:line via inspect.unwrap of the dash wrapper, single/multi Output, dict (pattern-matching) ids, clientside entries (no Python "callback" key), state omitted when empty, sorted by location (6 tests)
│   ├── test_macro_data.py           # curated macro catalog integrity: namespaces, 26 CAPE countries, overlay mapping covers all 6 INFL currencies (ECB=MRO), defaults ⊆ catalogs, filter_known URL guard (9 tests)
│   ├── test_macro_mocks.py          # PicklableInflation/Rate/Indicator API surface (all data members are attributes, only describe() a method), rolling_inflation starts at the 12th month (window alignment regression), pickle round-trips (6 tests)
│   ├── test_macro_objects.py        # cached accessors wire get_or_create: obj_type per class, date bounds into ctor, TTL_ASSET_LIST (3 tests)
│   ├── test_macro_stats.py          # describe-table outer merge on (property, period) incl. mismatched full-period rows; stats grid percent/decimal formatter wiring, sortable=False, suppressFieldDotNotation (6 tests)
│   └── test_macro_link.py           # macro shareable links: defaults omitted, (value, default) extra params, rates flag (4 tests)
├── component/               # @pytest.mark.component — Dash callbacks with mocked okama
│   ├── conftest.py                  # session-scoped Dash app + patched_okama_portfolio
│   ├── test_portfolio_callbacks.py  # pie chart, deviation toggle, cashflow strategies (6 types),
│   │                                # _resolve_indexation + _resolve_discount_rate (percent ÷100),
│   │                                # survival stats visibility,
│   │                                # CWD threshold validation, disable Add button logic,
│   │                                # percentage input lives in cash-flow frequency row,
│   │                                # custom cash flows in all strategies: _build_ts_dict parsing,
│   │                                # _apply_custom_time_series on every strategy, nested accordion
│   │                                # (collapsed default, closed on switch to non-TS, expanded for TS/URL
│   │                                # prefill, ts-plain chrome-less mode for the TS strategy; row container
│   │                                # empty while collapsed, on expand one example withdrawal row for the
│   │                                # TS strategy / one blank row for every other strategy),
│   │                                # MC limits validation: check_validity_monte_carlo (n≤MC_PORTFOLIO_MAX,
│   │                                # years 1..MC_PORTFOLIO_YEARS_MAX, n×years≤MC_PORTFOLIO_BUDGET, out-of-range
│   │                                # string flagged not crashed) + submit gated on mc-years validity,
│   │                                # amount inputs (#17): Initial/Cash flow amount are dmc.NumberInput
│   │                                # (thousandSeparator=" ", min=1 kept, MantineProvider wrap, URL string
│   │                                # prefill coerced to number, bad prefill → default),
│   │                                # print_weights_sum returns one plain string (single children Output —
│   │                                # a (text, flag) tuple leaks True into children, invalid ReactNode) (111 tests)
│   ├── test_ef_callbacks.py         # normalize_plot_types, resolve_return_column,
│   │                                # portfolio_weights, expand_weights, show/hide callbacks,
│   │                                # copy-link carries rebal / omits default month,
│   │                                # layout guard: no Y-axis (mean type) selector — EF always plots CAGR (28 tests)
│   ├── test_ef_click_find.py        # display_click_data (incl. backtest link carries the EF object's rebalancing period; clicked point renders a Selected portfolio card with trace-name badge + Sharpe from rf-rate; re-submit resets the section — stale clickData must not meet a changed ticker set; length-mismatch guard renders the unavailable note), find_portfolio (renders an Optimized portfolio card, None stats skipped) (25 tests)
│   ├── test_ef_url_portfolio.py     # URL portfolio handoff: _parse_url_portfolio (weights+symbol → store), get_portfolio_point (cached ok.Portfolio → percent risk/CAGR), prepare_ef star trace (label, JSON-list customdata), update_ef_cards wiring (payload on ticker match, None on mismatch, failure isolation) (17 tests)
│   ├── test_portfolio_go_to_ef.py   # Go to EF link (create_link params, defaults omitted, empty rows skipped) + gating (Copy-Link conditions OR <2 unique tickers) (6 tests)
│   ├── test_database_callbacks.py   # db_search: search results, empty, namespace routing; dag.AgGrid assertions (6 tests)
│   ├── test_dump_callbacks_script.py  # tools/dump_callbacks.py runs by path as a subprocess and dumps the full wiring map (sys.path guard) (1 test)
│   ├── test_compare_data_callback.py  # update_graf_compare: wealth/cumulative_return/annual_return(bar, CAGR subtitle)/cagr/correlation, stats (dag.AgGrid), errors; wealth annotations in points vs cumulative_return percent; stats grid suppressFieldDotNotation + formatPercentGuarded wiring (13 tests)
│   ├── test_benchmark_data_callback.py  # update_graf_benchmark: 6 plot types, bar chart, errors (10 tests)
│   ├── test_ef_data_callback.py       # update_ef_cards: figures, ef_points×100, mobile, errors, grid trace, grid/MC mode resolution, return_type always Geometric (no mean-type State), trace-names store for the click badge; customdata must serialize as JSON lists, not numpy/base64 — plotly>=6 drops numpy customdata from clickData (11 tests)
│   ├── test_ef_grid_callbacks.py     # sim-mode visibility, dynamic grid step options, grid↔pairwise exclusivity, submit gating (6 tests)
│   ├── test_portfolio_data_callback.py  # _update_graf_portfolio_inner: figure, y-titles (incl. annual_return, cumulative_return), weights, discount-rate wiring to dcf (÷100), errors; get_pf_figure annual_return bar chart (bars + CAGR return_type/subtitle); cumulative_return ts plot (percent annotations, title); wealth last-value annotations in balance points (zip-strict guard); update_graf_portfolio outer (toast, arity); show_graf_and_statistics_rows (reveal on submit); MC forecast scenarios end at zero then break; statistics grid: dag.AgGrid, suppressFieldDotNotation, formatPercentGuarded wiring; MC survival/wealth stats sections tabbed (#18): Table + Distribution tabs (renamed builders get_forecast_*_statistics_section), histograms of the MC series (survival offset series, FV/PV overlay with shared bins, constant-series bin guard), export grid ids preserved, mobile config routing via adopt_small_screens, empty-forecast stays table-only, wealth series fetched with include_negative_values=False (depleted balance is 0, never negative); compact single column on mobile (is_small_screen), desktop two-pane preserved; CashFlow IRR section (#19): percentiles + Min/Max/Mean/Std of monte_carlo_irr() + Historical IRR row (NaN→None), NaN paths excluded with an "n of N paths" note, all-NaN renders a graceful note (no tabs), percent formatter wiring, histogram of the non-NaN series with .1% ticks, inner returns the section before chart data (arity 7; outer toast at 7/8) (51 tests)
│   ├── test_mc_params_callbacks.py   # MC distribution parameters: set_mc_parameters wiring, submit tuple build, show_hide_param_groups, collapse toggle, hide_monte_carlo_rows (6 rows, incl. cumulative_return), reactive auto_estimate_distribution_parameters (gates, norm/lognorm/t fit, VaR-level df optimize + reset-on-clear, errors), df>2 validation; URL params prefill and survive reactive auto-estimate, dcc.Store round-trip (25 tests)
│   ├── test_grid_export.py           # xlsx export: button, rowdata_to_xlsx_download (PreventUpdate on empty rows AND on n_clicks=None — dynamically rendered export buttons fire their callback on first mount, must not auto-download), page callbacks return dcc.send_bytes dict; Excel number formats mirror grid formatters (column_formats percent/decimal/int, percent_column_formats helper, all 5 export callbacks wired — read back via openpyxl) (24 tests)
│   ├── test_grid_sorting.py          # column sorting disabled in every AG Grid: defaultColDef wiring asserted on all 13 grids across 6 files (database ×2, assets names/info, compare stats, pf stats, K-S distribution, MC survival/wealth/cash-flow-IRR desktop+compact) (9 tests)
│   ├── test_url_ccy_normalization.py # ccy in shared URLs prefills the currency dropdown on all 4 page forms: lowercase → uppercase, unknown → page default via resolve_url_currency (dcc.Dropdown silently clears values missing from options → ccy=None → okama "None.FX" 404) (7 tests)
│   ├── test_submit_spinner.py        # all 4 main data callbacks toggle the submit-button spinner via the `running` spec (chart's dcc.Loading is below the fold on mobile) (4 tests)
│   ├── test_compare_benchmark_callbacks.py  # change_style_for_hidden_row, show/hide,
│   │                                        # get_y_title (6 plot types), rolling-window disabled for annual_return + cumulative_return (compare + portfolio) (21 tests)
│   ├── test_macro_cards.py          # shared card factories: page-prefixed ids, multiselect defaults, copy-link guard, dates_ready keystroke guard, chart-card class (6 tests)
│   ├── test_macro_inflation_figures.py  # inflation figure builders: annual grouped bars / rolling / cumulative / monthly ×100, key-rate overlay (step-dot traces via catalog mapping), purchasing-power cards (7 tests)
│   ├── test_macro_inflation_page.py  # /macro/inflation page: REACTIVE main callback (every control an Input, no Submit; figure+PP cards+grid, PP rows dropped), overlay gating by plot type, half-typed-date guard, URL prefill, link/export/copy-link-guard callbacks (15 tests)
│   ├── test_macro_rates_page.py     # /macro/rates: step-lines (hv) with catalog labels, ×100, reactive Inputs wiring + date guard, prefill, link, export guard, copy-link guard (12 tests)
│   └── test_macro_cape10_page.py    # /macro/cape10: history lines (raw decimals), 26-country snapshot (sorted, cached per month, highlight colors, x-range headroom for outside labels, mobile keeps country ticks outside), decimal formatter, reactive Inputs wiring + date guard, PreventUpdate guard (16 tests)
└── e2e/                     # @pytest.mark.e2e — Playwright browser tests (Chromium)
    ├── conftest.py                  # Gunicorn server (TESTING=1, 2 workers) + Playwright
    ├── test_portfolio_page.py       # page load (5 controls), navigation (5 pages),
    │                                # mobile viewport 375px (Portfolio + EF),
    │                                # EF info panel renders assets names + info for URL tickers (#13 guard) (9 tests)
    ├── test_shareable_links.py      # shareable links: tickers + dates for all 4 pages; Portfolio fresh link (no MC URL params) → reactive estimation auto-fills the MC distribution fields (dead-callback regression guard); Portfolio Go to EF link → EF prefill (6 tests)
    ├── test_submit_interaction.py   # Submit → chart with real traces for all 4 pages; Portfolio stats grid: dotted column renders values, percent-formatted (6 tests)
    └── test_macro_pages.py          # macro pages AUTO-RENDER chart without Submit (bars/step-lines/history counts scoped to .cartesianlayer — rangeslider duplicates traces), stats grid percent via real DOM (formatPercentGuarded blind-spot coverage), navbar dropdown navigation, URL prefill, mobile viewport (7 tests)
```

### Run commands

| Command | Scope | Tests | Duration |
|---------|-------|-------|----------|
| `poetry run pytest -m unit` | Pure logic | 240 | ~2s |
| `poetry run pytest -m component` | Dash callbacks | 435 | ~7s |
| `poetry run pytest -m e2e` | Playwright browser | 32 | ~82s |
| `poetry run pytest -q` | Everything | 707 | ~92s |
| `poetry run pytest -m "not e2e"` | Fast suite | 675 | ~9s |

**E2E server output must stay on DEVNULL.** The Gunicorn subprocess in `tests/e2e/conftest.py`
redirects stdout/stderr to `subprocess.DEVNULL` deliberately: with `PIPE` nobody drains the
pipes, so once app logging fills the 64 KiB buffer (~17 navigations, since reactive MC
estimation logs per page load) gunicorn blocks on write and every later request times out
(the 2026-06-04 "5 e2e timeouts" incident). If you need server logs for debugging, redirect
to a file in `tmp/` instead of `PIPE`.

### What's covered per page

| Page | Unit | Component | E2E |
|------|------|-----------|-----|
| **Portfolio** | create_link (cf_ts owned by all strategies + activity rule, inactive-strategy omission; MC params deliberately NOT in links), symbols, build_distribution_parameters, reactive-estimation gates, MC limits validation (n/years/budget) | callbacks (pie chart, cashflow×6, rebalancing, stats table → dag.AgGrid with dot-notation + percent-formatter wiring), update_graf_portfolio, annual_return bar chart, cumulative_return plot type, wealth last-value annotations in points, rolling-window gating, percent rate inputs (discount/indexation ÷100), discount-rate wiring to dcf, amount inputs as dmc.NumberInput with space thousands separator (#17: type, min, provider wrap, URL prefill coercion), custom cash flows in all strategies (_build_ts_dict, _apply_custom_time_series per strategy, nested accordion collapsed/expanded/force-open), MC distribution parameters (groups show/hide, collapse toggle, reactive background estimation + VaR-level df optimization, df>2 validation, set_mc_parameters wiring, URL prefill + store round-trip), MC survival/wealth stats sections tabbed: table + distribution histograms (#18), CashFlow IRR section: percentile table + IRR histogram, NaN-safe (#19), compact tables on mobile, xlsx export n_clicks guard + Excel number formats (describe percent, survival decimal, wealth grouped int), Go to EF link (href params + gating) | load, controls, mobile, shareable link (no MC params; reactive auto-estimate fills MC fields), submit→traces, Go to EF link → EF prefill |
| **Efficient Frontier** | adaptive grid step (ef_grid), chart label padding (centered labels), portfolio card builder (stat blocks, allocation bars) | helpers (normalize, resolve, weights, expand), show/hide, display_click_data, find_portfolio (both render portfolio cards — Selected with trace-name badge / Optimized with None-stat skipping — Sharpe from the rf-rate input; backtest link carries the EF object's rebalancing period, omits default month, tolerates legacy pickles), update_ef_cards (return_type hardwired to Geometric — Y-axis selector removed, chart always plots CAGR), simulation mode (visibility, grid step options, grid↔pairwise exclusivity, submit gating), grid trace, customdata JSON-list serialization (plotly>=6 clickData regression), URL portfolio handoff (store parse, cached point, star trace, ticker-match rule, error isolation) | load, mobile, shareable link, submit→chart, info panel (assets names + info, #13 guard) |
| **Compare** | — | show/hide, update_graf_compare (wealth/cumulative_return/annual_return bar/cagr/correlation, stats table → dag.AgGrid with dot-notation + percent-formatter wiring), wealth annotations in points, rolling-window gating, xlsx export percent formats | load, shareable link, submit→traces |
| **Benchmark** | — | show/hide, get_y_title, update_graf_benchmark (6 plot types) | load, shareable link, submit→traces |
| **Database** | — | db_search (results, empty, namespace routing, ticker drop) → dag.AgGrid | load |
| **Macro (Inflation / Rates / CAPE10)** | catalog integrity + overlay mapping (ECB=MRO), cached accessors wiring, describe-merge + grid formatters, link builder, mocks API surface | per-page REACTIVE main callbacks (every control an Input, no Submit; half-typed-date guard) + error annotation, overlay gating, snapshot (26 countries, monthly cache, highlight + mobile outside ticks), URL prefill via filter_known, Copy-link guard, xlsx export n_clicks guard | auto-render w/o Submit (3 pages), stats grid percent via DOM, navbar dropdown, prefill, mobile |
| **common/ & tools/** | validators, math, create_link, symbols, object_cache (incl. TESTING isolation), chart_helpers (add_return_type_subtitle, format_points), dump_callbacks (callback wiring map formatter) | change_style_for_hidden_row, grid_export (xlsx via dcc.Download + rowdata_to_xlsx_download; Excel number formats mirror the on-page grid formatters), grid sorting disabled on every AG Grid (all 6 grid-building files) | — |

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
- **Macro pages are chart-first and fully reactive.** `/macro/*` pages use a one-row control bar above the chart (no controls/info card pair, no Submit button) and recalculate on every control change: all controls are Inputs of the main callback, which also omits `prevent_initial_call` so the chart renders on page load. `dates_ready` guards against half-typed YYYY-MM dates reaching okama; an empty series selection keeps the last chart (PreventUpdate) and disables Copy link. The control row is top-aligned (`align="start"`) so all 38px controls share one line while the dates' FormText hangs below.
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

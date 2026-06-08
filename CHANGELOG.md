# Changelog

All notable changes to okama-dash (the okama.io financial widgets) are documented
in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the version lives in `pyproject.toml`. This changelog starts at 4.0.0 — earlier
releases predate it.

## [4.5.0] — 2026-06-08

The Macro section arrives (inflation, central-bank rates, CAPE10, Russian real
estate), the Portfolio hands off to Compare/Benchmark/EF, and a Find max
withdrawal solver answers "how much can I safely withdraw?". 112 commits on top
of 4.0.0; the test suite grew to 889.

### Added

**Macro — a new chart-first section at `/macro/*`**

- Inflation: annual / rolling / cumulative / monthly-bar views across
  currencies, an optional key-rate overlay, purchasing-power cards, and
  headline stats (max 12-month, compound, annual) over the full period.
- Rates: central-bank key rates as stepped lines, real rates (nominal −
  trailing-12-month inflation) and a current-rate snapshot bar.
- CAPE10: 25-country current snapshot (default) and historical lines.
- Real Estate: Russian residential price per m² in RUB/USD and
  wealth-vs-inflation (reachable by URL).
- Every macro page recalculates reactively (no Submit) and carries a
  **Download data** link under each chart; a Macro dropdown joins the navbar.

**Portfolio**

- "Go to" dropdown hands the current portfolio to Efficient Frontier, Compare
  and Benchmark, carrying it in the URL; Compare and Benchmark prefill it as a
  chip alongside their own assets, with the rebalancing deviations (#23).
- Find max withdrawal: a solver that finds the maximum sustainable withdrawal
  toward a goal — keep purchasing power (PV), keep nominal balance (FV), or
  survive N years — at a chosen percentile (#22).
- Thousands separators on the remaining amount inputs (CWD/VDS/custom
  cash-flow rows) (#17).

### Changed

- Custom cash flows now use the same clickable chevron + collapse as Find max
  withdrawal (the Custom Time Series strategy keeps its plain bordered block).
- Rate charts clip to 2000 to avoid the Russian 1990s hyperinflation distorting
  the axis.

### Fixed

- Real rates with no inflation-mapped series show a clear message instead of an
  empty chart; the monthly inflation bar highlights each country's last
  published month; EUR purchasing-power no longer shows NaN.
- "Go to" links tolerate empty/string weights without blanking the EF link.

## [4.0.0] — 2026-06-06

Major release: 182 commits on top of 3.0.0. The stack moved to pandas 3.0,
Plotly 6.8 and okama 2.2.0; Portfolio rebalancing and cash flows were rebuilt
from the ground up; every table migrated to Dash AG Grid; and the app is now
guarded by a 565-test pyramid (unit / component / Playwright e2e).

### Added

**Portfolio**
- Rebalancing controls: period selector plus absolute/relative deviation
  thresholds, wired to okama `Rebalance` (fixes silently ignored rebalancing
  settings in 3.x).
- Five cash-flow strategies — Fixed Amount (Indexation), Fixed Percentage,
  Custom Time Series, Vanguard Dynamic Spending (VDS), Cut Withdrawals if
  Drawdown (CWD) — each with conditional UI and custom cash-flow entries
  (deposits/withdrawals time series) available in every strategy.
- Monte Carlo distribution parameters block (Normal / Lognormal / Student's t)
  with reactive background estimation from portfolio data, df > 2 validation
  and VaR-level df optimization.
- Monte Carlo settings and parameter overrides carried in shareable links;
  URL params survive reactive re-estimation.
- "Go to EF" button hands the portfolio off to the Efficient Frontier page.
- Annual Return (CAGR) bar chart and Cumulative Return plot types (also on
  Compare); wealth-index last-value annotations; survival statistics tables.
- Add/remove asset rows; weight range validation; percent-based rate inputs
  for indexation and discount rates.

**Efficient Frontier**
- Grid simulation mode: portfolios on an adaptive weight grid (step auto-scales
  with ticker count) as an alternative to pairwise Monte Carlo.
- Clicked frontier point renders a "Selected portfolio" card with stats,
  trace badge, Sharpe ratio (from the risk-free rate input) and allocation
  bars; "Find portfolio" renders an "Optimized portfolio" card.
- Portfolio handed off from the Portfolio page is drawn as a star point on
  the frontier while the ticker set matches.
- Backtest links carry the EF object's rebalancing period.

**All pages**
- Tables migrated to Dash AG Grid (statistics, forecast, database search,
  asset info) with consistent formatting and column sorting disabled.
- XLSX export via `dcc.Download` with Excel number formats mirroring the
  on-page grids (percent / decimal / grouped integers).
- Mobile overhaul: full-bleed charts with the legend below the plot, y-ticks
  inside, stacked cards, single-column MC statistics tables.
- Submit-button spinner while a chart is computing; unified 38px control
  heights and vertical rhythm across all forms.
- Currency from shared URLs is validated against the currency list and
  normalized (lowercase `ccy` no longer breaks pages).
- Unified two-layer caching for okama objects across pages; the currency
  list is memoized for 30 days.

**Development**
- Test suite: 565 tests — unit, component (mocked okama) and Playwright e2e
  against a Gunicorn server with picklable mocks.
- `tools/dump_callbacks.py`: greppable map of all Dash callbacks
  (file:line, outputs, inputs, states) from the runtime registry.
- `AGENTS.md` with project conventions; ruff replaces flake8 (zero findings).

### Changed

- pandas 2.x → **3.0**, Plotly 5.24 → **6.8**, okama → **2.2.0**,
  Python baseline ≥ 3.11 (developed on 3.14).
- The EF chart always plots CAGR — the Y-axis (mean type) selector is gone.
- Cash-flow rates are entered as percentages (0–100) instead of fractions.
- Monte Carlo parameter estimation is reactive — the explicit
  Estimate/Optimize buttons were removed.
- Shareable links got a diet: default values and inactive cash-flow
  strategies are omitted; MC and cash-flow params are grouped.

### Fixed

- Rebalancing settings were silently ignored on the Portfolio page (3.x bug).
- Plotly 6 dropped numpy `customdata` from `clickData` — EF click handling
  serializes to JSON lists (upstream plotly.py#5119 worked around app-side).
- Stale `clickData` after re-submit with a changed ticker set crashed the
  Selected-portfolio card.
- Wealth-chart last-value annotations crashed on every submit (zip-strict
  guard); MC forecast scenario lines now end exactly at zero on portfolio
  death instead of drawing along the axis.
- Object-cache filenames over the filesystem `NAME_MAX` are hashed;
  TESTING runs no longer poison the production cache.
- AG Grid value formatters moved to real JS (`dashAgGridFunctions.js`) —
  dotted ticker columns (e.g. `SPY.US`) render values again.
- Lowercase or unknown `ccy` URL params fall back to the page default
  instead of producing okama 404s.
- Withdrawal rate is computed from the actual cash-flow frequency;
  discount rate entered by the user is applied to DCF and the cache key.

[4.5.0]: https://github.com/mbk-dev/okama-dash/compare/v4.0.0...v4.5.0
[4.0.0]: https://github.com/mbk-dev/okama-dash/compare/e9e5731...v4.0.0

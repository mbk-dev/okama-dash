---
name: test_server_load
description: Use when measuring okama-dash server speed/load under Portfolio Monte Carlo or Efficient Frontier requests — sizing MC/EF limits, "how slow is submit", "how heavy is this scenario", or checking a setting change against server timing/RAM. Covers secondvds (prod) and local runs.
---

# Testing okama-dash server load

## Overview

The heavy work on okama.io is **not** the page GET — it is the Submit data
callback (`update_graf_portfolio` on `/portfolio`, `update_ef_cards` on `/`),
a POST to `/_dash-update-component` gated on the button's `n_clicks`. URL params
only prefill the form. So measure the **callback**, not the page.

**Primary tool: `tools/bench_server.py`** — it already replicates those callbacks
phase by phase (okama compute → `px.line` figure → store JSON → stats tables →
figure JSON), in-process, no payload to capture. Use it first. Do **not**
hand-roll an `ab`/`wrk`/`hey` HTTP harness unless you specifically need
concurrency saturation (see below) — that path needs captured POST bodies and is
far more fragile.

## When to use

- Choosing/justifying `MC_PORTFOLIO_MAX`, `MC_PORTFOLIO_BUDGET`, `MC_EF_MAX`,
  `GRID_POINT_BUDGET` (`common/settings.py`).
- "Why is Portfolio submit slow with Monte Carlo?" / "How heavy is N tickers on EF?"
- Checking a code/settings change against server time, payload size, peak RSS.

Not for: functional correctness (that's the mocked pytest suite), or client-only
CSS/layout (use the live page).

## The tool

```bash
# Local sanity run (no Redis, small matrix):
OKAMA_CACHE_BACKEND=filesystem poetry run python tools/bench_server.py --mode portfolio --quick

# Full matrix locally (Portfolio grid + EF construct/MC/grid):
OKAMA_CACHE_BACKEND=filesystem poetry run python tools/bench_server.py --mode all
```

Each measurement prints one JSON line and is also saved to
`tmp/bench_results_<host>.json`. Key fields: `total_callback_s`,
`t_figure_s` (∝ number of MC paths, the usual dominator), `t_fig_json_s`,
`fig_gz_mb`/`store_gz_mb` (payload, ∝ paths × years — billed twice: figure +
dcc.Store), `rss_peak_mb`, `mem_avail_mb`. EF rows: `t_construct_efpoints_s`,
`t_mc_s`, `t_grid_s`.

Extend the matrix by editing `bench_pf_combo` calls / `mc_ns` / asset-set lists
in the script. `verify_symbols` skips any ticker that 404s, so only real okama
symbols are measured.

## Running on prod (secondvds)

Real numbers come from the prod box. **Requires the user to approve prod access**
(naming secondvds). Then:

```bash
scp tools/bench_server.py secondvds:/var/www/okama-dash/tmp/bench_server.py
ssh secondvds 'free -m | head -2; uptime'                 # need ≳400 MB free, low load
ssh secondvds 'cd /var/www/okama-dash && nice -n 19 poetry run python tmp/bench_server.py --mode all' \
  | tee tmp/bench_secondvds.log
```

The script is single-process and `nice -19`; it competes for CPU with the live
site but does **not** add gunicorn concurrency. It has a `mem_available_mb()`
guard that skips a combo if free RAM drops below 350 MB. Clean up after:

```bash
ssh secondvds 'rm -f /var/www/okama-dash/tmp/bench_server.py /var/www/okama-dash/tmp/bench_results_secondvds.json'
```

## Client-side render time (the other half)

Server time ≠ what the user feels. A big figure (e.g. 500 paths × 50y ≈ 7 MB
gzip) costs seconds of browser parse/render. Measure with Playwright against a
local 2-worker Gunicorn (mirrors e2e), filling the MC fields and timing
click → traces drawn:

```bash
OKAMA_CACHE_BACKEND=filesystem poetry run gunicorn run_gunicorn:server \
  --workers 2 --bind 127.0.0.1:8061 --timeout 240 &
# then drive http://127.0.0.1:8061/portfolio?tickers=... with browser_run_code_unsafe,
# fill #pf-monte-carlo-number / #pf-monte-carlo-years, click #pf-submit-button,
# time waitForResponse(...pf-wealth-indexes.figure) → resp.finished() → gd.data populated.
```

Wait on `gd.data.length` (the Plotly graph div), **not** `.scatterlayer .trace`
DOM nodes — charts >1000 points become `scattergl` (WebGL, no per-trace SVG).
Kill the bench gunicorn afterwards (`pkill -f 'bind 127.0.0.1:8061'`).

## Concurrency saturation (advanced, prod-risky)

`bench_server.py` measures one request's cost. The prod ceiling is **3 gunicorn
workers, timeout 240 s** — only 3 heavy requests compute at once; the rest queue.
To find that ceiling you need real concurrent POSTs to
`/_dash-update-component` (capture a Submit body via DevTools "Copy as cURL",
then `hey -c {1,3,5,10}`). This degrades the live site and is **not** the default
— only with explicit user approval, in a low-traffic window, varying params so
the cache (`cache-directory/*.pkl` + Redis) doesn't mask compute. Clean cache
after: `find cache-directory -name '*.pkl' -delete` + `poetry run python clear_redis_cache.py`.

## Common mistakes

| Mistake | Reality |
|---------|---------|
| Load-testing the page URL with GET | Submit is a POST callback; GET only renders HTML. Measure the callback. |
| Re-building an HTTP harness from scratch | `tools/bench_server.py` already does the per-request breakdown. Use it first. |
| Same params every iteration | Cache serves repeats for free → you measure cache, not compute. Vary params / cold-clear. |
| Waiting on SVG `.trace` nodes | scattergl renders to canvas; poll `gd.data` instead. |
| Running on prod without cleanup | `cache-directory/` bloats (precedent: 18k pkl); remove the scp'd script + results. |
| Trusting numbers under load | Note free RAM and host load before/after; the script logs `mem_avail_mb` and `rss_peak_mb`. |

## Notes

`tools/bench_server.py` is deliberately **untested** and imports the real `app`
+ hits the real okama API — keep it out of the mocked pytest suite. See project
memory `performance-benchmark-mc-2026-06` for the 2026-06-06 baseline matrices
this skill produced, and `ef-grid-portfolios` for the EF budget rationale.

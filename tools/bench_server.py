"""Benchmark the server-side cost of Portfolio Monte Carlo and EF scenarios.

Replicates the exact code path of the Portfolio data callback
(`update_graf_portfolio`) phase by phase, and the EF data path
(`get_or_create_ef_object` / `get_monte_carlo` / `get_grid_portfolios`).

Run from the project root inside the project venv:

    # laptop sanity run (no Redis needed):
    OKAMA_CACHE_BACKEND=filesystem poetry run python tools/bench_server.py --mode portfolio --quick

    # production server (secondvds; copy the script to the server's tmp/ first):
    cd /var/www/okama-dash && nice -n 19 poetry run python tmp/bench_server.py --mode all

Results are printed incrementally (one JSON line per measurement) and saved to
tmp/bench_results_<host>.json. See .claude/skills/test_server_load/SKILL.md for
the full workflow and safety rules. Deliberately untested: it imports the real
`app` and hits the real okama API -- keep it out of the mocked test suite.
"""

import argparse
import gc
import gzip
import json
import os
import platform
import resource
import sys
import time

import pandas as pd

# The script lives in tools/ (or the server's tmp/) -- make the project root importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app  # noqa: F401, E402  -- initializes Dash app, cache and pages exactly as production does

import okama as ok

from common import settings
from common.ef_grid import predicted_grid_points, resolve_grid_step
from pages.portfolio.portfolio import (
    get_forecast_survival_statistics_table,
    get_forecast_wealth_statistics_table,
    get_pf_figure,
)

PF_SYMBOLS = ["SPY.US", "AGG.US", "GLD.US"]  # verified real symbols (okama docstrings)
PF_WEIGHTS = [0.60, 0.35, 0.05]

# Candidates for EF asset sets; each is verified against the real okama DB at runtime.
EF_CANDIDATES = [
    "SPY.US",
    "AGG.US",
    "GLD.US",
    "AAPL.US",
    "MSFT.US",
    "GOOG.US",
    "AMZN.US",
    "JPM.US",
    "JNJ.US",
    "XOM.US",
    "PG.US",
    "KO.US",
    "WMT.US",
    "MCD.US",
    "V.US",
]

RESULTS: list[dict] = []


def now() -> float:
    return time.perf_counter()


def rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def mem_available_mb() -> float:
    """System-wide available memory; guards against OOMing a small prod host."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    return float("inf")


def emit(row: dict) -> None:
    RESULTS.append(row)
    print(json.dumps(row, default=str), flush=True)


def make_pf(withdrawal: bool = False) -> ok.Portfolio:
    """Portfolio configured the way the callback's _construct_portfolio does."""
    pf = ok.Portfolio(
        assets=PF_SYMBOLS,
        weights=PF_WEIGHTS,
        ccy="USD",
        inflation=True,
        rebalancing_strategy=ok.Rebalance(period="year"),
        symbol="bench_portfolio.PF",
    )
    ind = ok.IndexationStrategy(pf)
    ind.initial_investment = settings.INITIAL_INVESTMENT_DEFAULT
    if withdrawal:
        ind.amount = -40  # 4% of initial, the classic withdrawal-rate scenario
        ind.frequency = "year"
    else:
        ind.amount = 0
    pf.dcf.cashflow_parameters = ind
    pf.dcf.use_discounted_values = True
    return pf


def bench_pf_combo(pf: ok.Portfolio, n: int, years: int, dist: str, label: str) -> None:
    # Phase 0: raw okama MC compute, cold (what dcf.monte_carlo_wealth costs alone)
    pf.dcf.set_mc_parameters(distribution=dist, distribution_parameters=None, period=years, mc_number=n)
    pf.dcf._monte_carlo_wealth_fv = pd.DataFrame()  # ensure cold state
    t0 = now()
    df_mc = pf.dcf.monte_carlo_wealth(discounting="fv", include_negative_values=False)
    t_mc = now() - t0

    # Phase 1: the full figure path exactly as the callback runs it.
    # get_pf_figure calls set_mc_parameters internally, which invalidates the MC
    # caches, so this includes a fresh MC compute + backtest + nullify + px.line.
    t0 = now()
    fig, df_backtest, df_forecast, df_data = get_pf_figure(
        pf,
        "wealth",
        True,  # inflation_on
        2,  # rolling_window (unused for wealth)
        n,
        years,
        dist,
        "yes",  # show_backtest
        False,  # log_scale
        "indexation",
        distribution_parameters_monte_carlo=None,
    )
    t_fig = now() - t0

    # Phase 2: chart-data store JSON (goes to dcc.Store in the same response)
    t0 = now()
    store_json = df_data.to_json(orient="split", default_handler=str)
    t_store = now() - t0

    # Phase 3+4: MC statistics tables (reuse the cached MC frame, as in prod)
    t0 = now()
    get_forecast_survival_statistics_table(df_forecast, df_backtest, pf, compact=False)
    t_surv = now() - t0
    t0 = now()
    get_forecast_wealth_statistics_table(pf, compact=False)
    t_wtbl = now() - t0

    # Phase 5: figure JSON serialization (proxy for Dash response encoding)
    t0 = now()
    fig_json = fig.to_json()
    t_figjson = now() - t0

    fig_bytes = len(fig_json.encode())
    fig_gz = len(gzip.compress(fig_json.encode(), 6))
    store_bytes = len(store_json.encode())
    store_gz = len(gzip.compress(store_json.encode(), 6))
    total = t_fig + t_store + t_surv + t_wtbl + t_figjson

    emit(
        {
            "bench": "portfolio",
            "label": label,
            "n": n,
            "years": years,
            "dist": dist,
            "t_mc_only_s": round(t_mc, 2),
            "t_figure_s": round(t_fig, 2),
            "t_store_json_s": round(t_store, 2),
            "t_surv_table_s": round(t_surv, 2),
            "t_wealth_table_s": round(t_wtbl, 2),
            "t_fig_json_s": round(t_figjson, 2),
            "total_callback_s": round(total, 2),
            "fig_mb": round(fig_bytes / 1e6, 1),
            "fig_gz_mb": round(fig_gz / 1e6, 1),
            "store_mb": round(store_bytes / 1e6, 1),
            "store_gz_mb": round(store_gz / 1e6, 1),
            "mc_rows": int(df_mc.shape[0]),
            "rss_peak_mb": round(rss_mb()),
            "mem_avail_mb": round(mem_available_mb()),
        }
    )
    # Release the big objects before the next combo (small prod host).
    del fig, fig_json, store_json, df_mc, df_data, df_forecast, df_backtest
    gc.collect()


def bench_portfolio(quick: bool) -> None:
    t0 = now()
    pf = make_pf()
    emit({"bench": "portfolio-construct", "t_construct_s": round(now() - t0, 2), "rss_peak_mb": round(rss_mb())})

    if quick:
        ns, yearss = [100, 1000], [10, 50]
    else:
        ns, yearss = [100, 500, 1000, 2000], [10, 20, 30, 50]

    for n in ns:
        for years in yearss:
            if mem_available_mb() < 350:
                emit({"bench": "portfolio", "label": "SKIPPED-low-mem", "n": n, "years": years})
                continue
            bench_pf_combo(pf, n, years, "norm", label="norm/no-cashflow")

    # Spot checks: distribution cost + a real withdrawal strategy
    spot_n, spot_years = (1000, 30) if not quick else (1000, 10)
    for dist in ["lognorm", "t"]:
        bench_pf_combo(pf, spot_n, spot_years, dist, label=f"{dist}/no-cashflow")
    pf_w = make_pf(withdrawal=True)
    bench_pf_combo(pf_w, spot_n, spot_years, "norm", label="norm/withdrawal-4pct")


def verify_symbols(candidates: list[str], needed: int) -> list[str]:
    good: list[str] = []
    for sym in candidates:
        try:
            ok.Asset(sym)
            good.append(sym)
        except Exception as exc:  # noqa: BLE001 -- 404 etc.: just skip the symbol
            print(f"# symbol {sym} skipped: {exc}", flush=True)
        if len(good) >= needed:
            break
    return good


def bench_ef_set(symbols: list[str], mc_ns: list[int], do_grid: bool) -> None:
    k = len(symbols)
    t0 = now()
    ef = ok.EfficientFrontier(
        symbols,
        ccy="USD",
        inflation=False,
        n_points=settings.EF_POINTS,
        full_frontier=True,
        rebalancing_strategy=ok.Rebalance(period="year"),
    )
    _ = ef.ef_points
    t_construct = now() - t0
    emit(
        {
            "bench": "ef-construct",
            "k_assets": k,
            "symbols": ",".join(symbols),
            "t_construct_efpoints_s": round(t_construct, 2),
            "rss_peak_mb": round(rss_mb()),
        }
    )

    for n in mc_ns:
        t0 = now()
        df = ef.get_monte_carlo(n=n)
        emit(
            {
                "bench": "ef-mc",
                "k_assets": k,
                "n": n,
                "t_mc_s": round(now() - t0, 2),
                "points": int(df.shape[0]),
                "rss_peak_mb": round(rss_mb()),
            }
        )

    if do_grid:
        step = resolve_grid_step(k)
        t0 = now()
        df = ef.get_grid_portfolios(step=step, max_points=settings.GRID_POINT_BUDGET)
        emit(
            {
                "bench": "ef-grid",
                "k_assets": k,
                "step": step,
                "predicted_points": predicted_grid_points(k, step),
                "t_grid_s": round(now() - t0, 2),
                "points": int(df.shape[0]),
                "rss_peak_mb": round(rss_mb()),
            }
        )


def bench_ef(quick: bool) -> None:
    verified = verify_symbols(EF_CANDIDATES, needed=12)
    print(f"# verified EF symbols: {verified}", flush=True)
    if quick:
        bench_ef_set(verified[:2], mc_ns=[1000], do_grid=True)
        bench_ef_set(verified[:6], mc_ns=[1000], do_grid=True)
    else:
        bench_ef_set(verified[:2], mc_ns=[1000, 5000], do_grid=True)
        bench_ef_set(verified[:6], mc_ns=[1000, 5000], do_grid=True)
        bench_ef_set(verified[:12], mc_ns=[5000], do_grid=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["portfolio", "ef", "all"], default="all")
    parser.add_argument("--quick", action="store_true", help="small matrix for a laptop sanity run")
    args = parser.parse_args()

    host = platform.node()
    emit(
        {
            "bench": "meta",
            "host": host,
            "python": sys.version.split()[0],
            "okama": ok.__version__,
        }
    )

    if args.mode in {"portfolio", "all"}:
        bench_portfolio(args.quick)
    if args.mode in {"ef", "all"}:
        bench_ef(args.quick)

    out_path = f"tmp/bench_results_{host}.json"
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"# saved {len(RESULTS)} rows to {out_path}", flush=True)


if __name__ == "__main__":
    main()

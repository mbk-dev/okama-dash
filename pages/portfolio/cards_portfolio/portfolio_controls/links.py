"""Shareable-link callbacks: the Copy-link builder (full portfolio + cash-flow
state) and the three 'Go to' hrefs (Efficient Frontier / Compare / Benchmark)."""

from typing import Optional

from dash import callback, ALL
from dash.dependencies import Input, Output, State

from common.create_link import create_link, scope_cashflow_params


@callback(
    Output("pf-show-url", "children"),
    Input("pf-copy-link-button", "n_clicks"),
    State("pf-url", "href"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    State("pf-base-currency", "value"),
    State("pf-first-date", "value"),
    State("pf-last-date", "value"),
    State("pf-rebalancing-period", "value"),
    # Rebalancing deviation
    State("pf-rebal-abs-deviation", "value"),
    State("pf-rebal-rel-deviation", "value"),
    # Cash flow strategy
    State("pf-initial-amount", "value"),
    State("pf-discount-rate", "value"),
    State("pf-ticker", "value"),
    State("pf-cf-strategy-type", "value"),
    State("pf-cf-frequency", "value"),
    State("pf-cf-amount", "value"),
    State("pf-cf-indexation", "value"),
    State("pf-cf-percentage", "value"),
    State("pf-cf-vds-percentage", "value"),
    State("pf-cf-vds-min-withdrawal", "value"),
    State("pf-cf-vds-max-withdrawal", "value"),
    State("pf-cf-vds-adjust-minmax", "value"),
    State("pf-cf-vds-floor", "value"),
    State("pf-cf-vds-ceiling", "value"),
    State("pf-cf-vds-adjust-fc", "value"),
    State("pf-cf-vds-indexation", "value"),
    State("pf-cf-cwd-amount", "value"),
    State({"type": "pf-cf-cwd-threshold", "index": ALL}, "value"),
    State({"type": "pf-cf-cwd-reduction", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-amount", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_link_pf(
    n_clicks: int,
    href: str,
    tickers_list: Optional[list],
    weights_list: Optional[list],
    ccy: str,
    first_date: str,
    last_date: str,
    rebal: str,
    # Rebalancing deviation
    abs_dev: Optional[float],
    rel_dev: Optional[float],
    # Cash flow strategy
    initial_amount: Optional[float],
    discount_rate: Optional[float],
    symbol: Optional[str],
    cf_strategy: str,
    cf_freq: str,
    cf_amount: Optional[float],
    cf_indexation: Optional[float],
    cf_pct: Optional[float],
    vds_pct: Optional[float],
    vds_min: Optional[float],
    vds_max: Optional[float],
    vds_adj_mm: bool,
    vds_floor: Optional[float],
    vds_ceil: Optional[float],
    vds_adj_fc: bool,
    vds_indexation: Optional[float],
    cwd_amount: Optional[float],
    cwd_thresholds: list,
    cwd_reductions: list,
    ts_dates: list,
    ts_amounts: list,
):
    cwd_tr = None
    if cwd_thresholds and cwd_reductions:
        pairs = [
            f"{t}:{r}" for t, r in zip(cwd_thresholds, cwd_reductions, strict=True) if t is not None and r is not None
        ]
        if pairs:
            cwd_tr = ",".join(pairs)

    cf_ts = None
    if ts_dates and ts_amounts:
        pairs = [f"{d}:{a}" for d, a in zip(ts_dates, ts_amounts, strict=True) if d and a is not None]
        if pairs:
            cf_ts = ",".join(pairs)

    # Scope cashflow params to active strategy only
    scoped_cf = scope_cashflow_params(
        cf_strategy=cf_strategy,
        cf_freq=cf_freq,
        cf_amount=cf_amount,
        cf_indexation=cf_indexation,
        cf_pct=cf_pct,
        vds_pct=vds_pct,
        vds_min=vds_min,
        vds_max=vds_max,
        vds_adj_mm=vds_adj_mm,
        vds_floor=vds_floor,
        vds_ceil=vds_ceil,
        vds_adj_fc=vds_adj_fc,
        vds_indexation=vds_indexation,
        cwd_amount=cwd_amount,
        cwd_tr=cwd_tr,
        cf_ts=cf_ts,
    )

    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        weights_list=weights_list,
        rebal=rebal,
        initial_amount=initial_amount,
        discount_rate=discount_rate,
        symbol=symbol,
        abs_dev=abs_dev,
        rel_dev=rel_dev,
        # scoped_cf carries cf_strategy too: None (omitted) when the selected
        # strategy has a zero primary flow value and no custom cash flows,
        # i.e. is effectively inactive.
        **scoped_cf,
    )


@callback(
    Output("pf-goto-ef", "href"),
    Output("pf-goto-compare", "href"),
    Output("pf-goto-benchmark", "href"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    Input("pf-base-currency", "value"),
    Input("pf-first-date", "value"),
    Input("pf-last-date", "value"),
    Input("pf-rebalancing-period", "value"),
    Input("pf-ticker", "value"),
    Input("pf-rebal-abs-deviation", "value"),
    Input("pf-rebal-rel-deviation", "value"),
)
def update_go_to_links(
    tickers_list: Optional[list],
    weights_list: Optional[list],
    ccy: str,
    first_date: str,
    last_date: str,
    rebal: str,
    symbol: Optional[str],
    abs_dev: Optional[float],
    rel_dev: Optional[float],
) -> tuple[str, str, str]:
    """Build the three "Go to" hrefs carrying the portfolio.

    EF keeps the page-level vocabulary (tickers define the frontier, weights +
    symbol are the portfolio section) — same as the EF "Backtest portfolio"
    link, in reverse. Compare/Benchmark take the portfolio as its own pf_*
    param group + ccy/dates, including the rebalancing deviations (abs/rel):
    their page-level tickers keep their own meaning, and no cash-flow params
    travel. EF gets the period only — okama's EfficientFrontier ignores the
    deviations (issue #23).
    """
    tickers = [t for t in tickers_list if t]
    # Drop cleared rows ("" from a blanked dcc number input) so create_link's
    # "{w:g}" pf_weights formatting can't raise on an empty string — this single
    # callback drives all three hrefs, so one raise would blank the EF link too.
    # Types are preserved (int/str), so the EF link's str(w) format is unchanged.
    weights = [w for w in weights_list if w not in (None, "")]
    ef_href = create_link(
        href="/",
        tickers_list=tickers,
        ccy=ccy,
        first_date=first_date,
        last_date=last_date,
        rebal=rebal,
        weights_list=weights,
        symbol=symbol,
    )
    handoff = {
        "tickers_list": [],
        "ccy": ccy,
        "first_date": first_date,
        "last_date": last_date,
        "pf_tickers": tickers,
        "pf_weights": weights,
        "pf_rebal": rebal,
        "pf_symbol": symbol,
        "pf_abs_dev": abs_dev,
        "pf_rel_dev": rel_dev,
    }
    return ef_href, create_link(href="/compare", **handoff), create_link(href="/benchmark", **handoff)

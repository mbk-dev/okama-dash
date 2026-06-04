import logging
import re
import time
import typing

import dash
import dash_bootstrap_components as dbc
import plotly
from dash import dash_table, callback, ALL, html, dcc
from dash.dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np
from scipy.stats import t, norm, lognorm, kstest, jarque_bera, skew, kurtosis as scipy_kurtosis

import okama as ok

import common.create_link
import common.settings as settings
import common.update_style
from common.chart_helpers import add_inflation_trace, add_crisis_rectangles, add_last_value_annotations, add_sharpe_ratio_row, add_return_type_annotation
from common.mobile_screens import adopt_small_screens
from common.object_cache import get_or_create, TTL_PORTFOLIO
from pages.portfolio.cards_portfolio.portfolio_controls import card_controls
from pages.portfolio.cards_portfolio.portfolio_description import card_portfolio_description
from pages.portfolio.cards_portfolio.portfolio_info import card_assets_info
from pages.portfolio.cards_portfolio.pf_statistics_table import card_table
from pages.portfolio.cards_portfolio.pf_wealth_indexes_chart import card_graf_portfolio

dash.register_page(
    __name__,
    path="/portfolio",
    title="Investment Portfolio : okama",
    name="Investment Portfolio",
    suppress_callback_exceptions=True,
    description="Okama.io widget for Investment Portfolio analysis",
)


def _parse_pair_csv(csv_str):
    if not csv_str:
        return None
    pairs = []
    for item in str(csv_str).split(","):
        parts = item.split(":", 1)
        if len(parts) == 2:
            pairs.append((parts[0].strip(), parts[1].strip()))
    return pairs or None


_MC_DATE_RE = re.compile(r"^\d{4}-\d{2}$")


def _valid_mc_date(date_str) -> bool:
    """Empty is OK (okama defaults apply); otherwise require the app's YYYY-MM format."""
    return date_str in (None, "") or bool(_MC_DATE_RE.match(date_str))


def _portfolio_is_complete(assets, weights) -> bool:
    """True when every constructor row has a ticker and a weight, and weights sum to 100%."""
    if not assets or not weights:
        return False
    if any(not a for a in assets) or any(w is None for w in weights):
        return False
    return abs(sum(weights) - 100.0) < 1e-6


def build_distribution_parameters(
    distribution: str,
    mu, sigma,
    shape, scale_ln,
    df, loc_t, scale_t,
) -> tuple | None:
    """Build okama Monte Carlo ``distribution_parameters`` from raw form values.

    Empty inputs become ``None`` so okama estimates them via ``.fit()``. For the
    lognormal distribution okama always forces ``loc = -1.0``, so it is injected
    here regardless of the form. Returns ``None`` when the user supplied no value
    (let okama estimate everything).
    """
    def _f(x):
        return float(x) if x not in (None, "") else None

    match distribution:
        case "norm":
            vals = (_f(mu), _f(sigma))
            return None if all(v is None for v in vals) else vals
        case "lognorm":
            shape_v, scale_v = _f(shape), _f(scale_ln)
            return None if (shape_v is None and scale_v is None) else (shape_v, -1.0, scale_v)
        case "t":
            vals = (_f(df), _f(loc_t), _f(scale_t))
            return None if all(v is None for v in vals) else vals
        case _:
            return None


def _build_ror_portfolio(assets, weights, ccy, first_date, last_date, rebal_period, abs_dev, rel_dev):
    """Build a cached Portfolio sufficient for fitting MC distribution parameters.

    Distribution fitting needs only ``pf.ror``, which depends on assets, weights,
    dates, currency and rebalancing — not on cash flow or discount rate.
    """
    assets = [a for a in assets if a is not None]
    weights = [w / 100.0 for w in weights if w is not None]
    abs_dev_val = float(abs_dev) / 100 if abs_dev else None
    rel_dev_val = float(rel_dev) / 100 if rel_dev else None

    def _construct():
        rebal_strategy = ok.Rebalance(period=rebal_period, abs_deviation=abs_dev_val, rel_deviation=rel_dev_val)
        return ok.Portfolio(
            assets=assets, weights=weights, first_date=first_date, last_date=last_date,
            ccy=ccy, rebalancing_strategy=rebal_strategy,
        )

    pf_object, _ = get_or_create(
        obj_type="portfolio",
        constructor_fn=_construct,
        cache_key_params={
            "symbols": assets, "weights": weights, "ccy": ccy,
            "first_date": first_date, "last_date": last_date,
            "rebal": rebal_period, "abs_dev": abs_dev, "rel_dev": rel_dev,
            "purpose": "mc_params",
        },
        ttl_seconds=TTL_PORTFOLIO,
    )
    return pf_object


def layout(
    tickers=None,
    weights=None,
    first_date=None,
    last_date=None,
    ccy=None,
    rebal=None,
    # advanced
    initial_amount=None,
    cashflow=None,
    discount_rate=None,
    symbol=None,
    # rebalancing deviation
    abs_dev=None,
    rel_dev=None,
    # cashflow strategy
    cf_strategy=None,
    cf_freq=None,
    cf_amount=None,
    cf_indexation=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    cwd_amount=None,
    cwd_tr=None,
    cf_ts=None,
    **kwargs,
):
    page = dbc.Container(
        [
            dbc.Toast(
                "",
                id="pf-error-toast",
                header="Validation Error",
                is_open=False,
                dismissable=True,
                duration=0,
                color="danger",
                style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999, "width": 350},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        card_controls(
                            tickers=tickers,
                            weights=weights,
                            first_date=first_date,
                            last_date=last_date,
                            ccy=ccy,
                            rebal=rebal,
                            initial_amount=initial_amount,
                            cashflow=cashflow,
                            discount_rate=discount_rate,
                            symbol=symbol,
                            abs_dev=float(abs_dev) if abs_dev else None,
                            rel_dev=float(rel_dev) if rel_dev else None,
                            cf_strategy=cf_strategy,
                            cf_freq=cf_freq,
                            cf_amount=float(cf_amount) if cf_amount else None,
                            cf_indexation=float(cf_indexation) if cf_indexation else None,
                            cf_pct=float(cf_pct) if cf_pct else None,
                            vds_pct=float(vds_pct) if vds_pct else None,
                            vds_min=float(vds_min) if vds_min else None,
                            vds_max=float(vds_max) if vds_max else None,
                            vds_adj_mm=vds_adj_mm != "0" if vds_adj_mm is not None else None,
                            vds_floor=float(vds_floor) if vds_floor else None,
                            vds_ceil=float(vds_ceil) if vds_ceil else None,
                            vds_adj_fc=vds_adj_fc == "1" if vds_adj_fc is not None else None,
                            vds_indexation=float(vds_indexation) if vds_indexation else None,
                            cwd_amount=float(cwd_amount) if cwd_amount else None,
                            cwd_tr=_parse_pair_csv(cwd_tr),
                            cf_ts=_parse_pair_csv(cf_ts),
                        ),
                        lg=5,
                    ),
                    dbc.Col(card_assets_info, lg=7),
                ]
            ),
            dbc.Row(
                dbc.Col(card_graf_portfolio, width=12), align="center", style={"display": "none"}, id="pf-graf-row"
            ),
            dbc.Row(
                dbc.Col(card_table, width=12),
                align="center",
                style={"display": "none"},
                id="pf-portfolio-statistics-row",
            ),
            dbc.Row(dbc.Col(card_portfolio_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="pf-wealth-indexes", component_property="figure"),
    Output(component_id="pf-wealth-indexes", component_property="config"),
    Output(component_id="pf-describe-table", component_property="children"),
    Output(component_id="pf-monte-carlo-statistics", component_property="children"),
    Output(component_id="pf-monte-carlo-wealth-statistics", component_property="children"),
    Output(component_id="pf-store-chart-data", component_property="data"),
    Output(component_id="pf-error-toast", component_property="is_open"),
    Output(component_id="pf-error-toast", component_property="children"),
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    # logarithmic scale button
    Input(component_id="pf-logarithmic-scale-switch", component_property="on"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    State(component_id="pf-base-currency", component_property="value"),
    State(component_id="pf-rebalancing-period", component_property="value"),
    State(component_id="pf-rebal-abs-deviation", component_property="value"),
    State(component_id="pf-rebal-rel-deviation", component_property="value"),
    State(component_id="pf-first-date", component_property="value"),
    State(component_id="pf-last-date", component_property="value"),
    # cash flow strategy parameters
    State(component_id="pf-initial-amount", component_property="value"),
    State(component_id="pf-discount-rate", component_property="value"),
    State(component_id="pf-ticker", component_property="value"),
    State(component_id="pf-cf-strategy-type", component_property="value"),
    State(component_id="pf-cf-frequency", component_property="value"),
    State(component_id="pf-cf-amount", component_property="value"),
    State(component_id="pf-cf-indexation", component_property="value"),
    State(component_id="pf-cf-percentage", component_property="value"),
    # VDS
    State(component_id="pf-cf-vds-percentage", component_property="value"),
    State(component_id="pf-cf-vds-min-withdrawal", component_property="value"),
    State(component_id="pf-cf-vds-max-withdrawal", component_property="value"),
    State(component_id="pf-cf-vds-adjust-minmax", component_property="value"),
    State(component_id="pf-cf-vds-floor", component_property="value"),
    State(component_id="pf-cf-vds-ceiling", component_property="value"),
    State(component_id="pf-cf-vds-adjust-fc", component_property="value"),
    State(component_id="pf-cf-vds-indexation", component_property="value"),
    # CWD
    State(component_id="pf-cf-cwd-amount", component_property="value"),
    State(component_id="pf-cf-cwd-indexation", component_property="value"),
    State({"type": "pf-cf-cwd-threshold", "index": ALL}, "value"),
    State({"type": "pf-cf-cwd-reduction", "index": ALL}, "value"),
    # TimeSeries
    State({"type": "pf-cf-ts-date", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-amount", "index": ALL}, "value"),
    # options
    State(component_id="pf-plot-option", component_property="value"),
    State(component_id="pf-inflation-switch", component_property="value"),
    State(component_id="pf-rolling-window", component_property="value"),
    # monte carlo
    State(component_id="pf-monte-carlo-number", component_property="value"),
    State(component_id="pf-monte-carlo-years", component_property="value"),
    State(component_id="pf-monte-carlo-distribution", component_property="value"),
    State(component_id="pf-monte-carlo-backtest", component_property="value"),
    # monte carlo distribution parameters
    State(component_id="pf-mc-norm-mu", component_property="value"),
    State(component_id="pf-mc-norm-sigma", component_property="value"),
    State(component_id="pf-mc-lognorm-shape", component_property="value"),
    State(component_id="pf-mc-lognorm-scale", component_property="value"),
    State(component_id="pf-mc-t-df", component_property="value"),
    State(component_id="pf-mc-t-loc", component_property="value"),
    State(component_id="pf-mc-t-scale", component_property="value"),
    prevent_initial_call=True,
)
def update_graf_portfolio(
    screen,
    n_clicks,
    log_on: bool,
    assets: list,
    weights: list,
    ccy: str,
    rebalancing_period: str,
    rebal_abs_deviation,
    rebal_rel_deviation,
    fd_value: str,
    ld_value: str,
    # Cash flow strategy parameters
    initial_amount: float,
    discount_rate: float,
    symbol: str,
    cf_strategy: str,
    cf_frequency: str,
    cf_amount: float,
    cf_indexation: float,
    cf_percentage: float,
    # VDS
    vds_percentage: float,
    vds_min_withdrawal: float,
    vds_max_withdrawal: float,
    vds_adjust_minmax: bool,
    vds_floor: float,
    vds_ceiling: float,
    vds_adjust_fc: bool,
    vds_indexation: float,
    # CWD
    cwd_amount: float,
    cwd_indexation: float,
    cwd_thresholds: list,
    cwd_reductions: list,
    # TimeSeries
    ts_dates: list,
    ts_amounts: list,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    # Monte Carlo
    n_monte_carlo: int,
    years_monte_carlo: int,
    distribution_monte_carlo: str,
    show_backtest: str,
    mc_norm_mu=None,
    mc_norm_sigma=None,
    mc_lognorm_shape=None,
    mc_lognorm_scale=None,
    mc_t_df=None,
    mc_t_loc=None,
    mc_t_scale=None,
):
    trigger = dash.ctx.triggered_id
    if trigger == "pf-logarithmic-scale-switch":
        patched_fig = dash.Patch()
        patched_fig["layout"]["yaxis"]["type"] = "log" if log_on else "linear"
        return (
            patched_fig,
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            dash.no_update, dash.no_update,
        )

    distribution_parameters_monte_carlo = build_distribution_parameters(
        distribution_monte_carlo,
        mc_norm_mu, mc_norm_sigma,
        mc_lognorm_shape, mc_lognorm_scale,
        mc_t_df, mc_t_loc, mc_t_scale,
    )

    try:
        result = _update_graf_portfolio_inner(
            screen, log_on, assets, weights, ccy, rebalancing_period,
            rebal_abs_deviation, rebal_rel_deviation, fd_value, ld_value,
            initial_amount, discount_rate, symbol, cf_strategy, cf_frequency,
            cf_amount, cf_indexation, cf_percentage,
            vds_percentage, vds_min_withdrawal, vds_max_withdrawal, vds_adjust_minmax,
            vds_floor, vds_ceiling, vds_adjust_fc, vds_indexation,
            cwd_amount, cwd_indexation, cwd_thresholds, cwd_reductions,
            ts_dates, ts_amounts,
            plot_type, inflation_on, rolling_window,
            n_monte_carlo, years_monte_carlo, distribution_monte_carlo, show_backtest,
            distribution_parameters_monte_carlo=distribution_parameters_monte_carlo,
        )
        return (*result, False, "")
    except Exception as e:
        logging.exception("Callback error")
        empty_fig = go.Figure()
        return (
            empty_fig, {}, dash_table.DataTable(), dash_table.DataTable(), dash_table.DataTable(), None,
            True, f"Error: {e}",
        )


@callback(
    Output(component_id="pf-graf-row", component_property="style"),
    Output(component_id="pf-portfolio-statistics-row", component_property="style"),
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State(component_id="pf-graf-row", component_property="style"),
)
def show_graf_and_statistics_rows(n_clicks, style):
    """Reveal the chart and statistics rows on submit.

    Kept separate from the slow ``update_graf_portfolio`` callback so the rows
    (and the ``dcc.Loading`` spinner they contain) become visible immediately
    on click, instead of only after the chart finishes computing. Mirrors the
    show-row callbacks on the compare, benchmark and efficient-frontier pages.
    """
    style = common.update_style.change_style_for_hidden_row(n_clicks, style)
    return style, style


@callback(
    Output(component_id="pf-mc-norm-mu", component_property="value"),
    Output(component_id="pf-mc-norm-sigma", component_property="value"),
    Output(component_id="pf-mc-lognorm-shape", component_property="value"),
    Output(component_id="pf-mc-lognorm-scale", component_property="value"),
    Output(component_id="pf-mc-t-df", component_property="value"),
    Output(component_id="pf-mc-t-loc", component_property="value"),
    Output(component_id="pf-mc-t-scale", component_property="value"),
    Output(component_id="pf-mc-params-message", component_property="children"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    Input(component_id="pf-base-currency", component_property="value"),
    Input(component_id="pf-first-date", component_property="value"),
    Input(component_id="pf-last-date", component_property="value"),
    Input(component_id="pf-rebalancing-period", component_property="value"),
    Input(component_id="pf-rebal-abs-deviation", component_property="value"),
    Input(component_id="pf-rebal-rel-deviation", component_property="value"),
    Input(component_id="pf-monte-carlo-distribution", component_property="value"),
    Input(component_id="pf-mc-t-var-level", component_property="value"),
    prevent_initial_call=True,
)
def auto_estimate_distribution_parameters(
    assets, weights, ccy, fd, ld, rebal, abs_dev, rel_dev, distribution, var_level,
):
    """Recompute Monte Carlo distribution parameters in the background.

    Fires when the portfolio definition changes (tickers, weights, dates,
    currency, rebalancing) or the distribution type is switched — re-fits the
    active distribution's parameters. A VaR-level change (Student's t only,
    non-empty level) re-optimizes df instead. No-op until the portfolio is
    complete: all constructor rows filled and weights summing to 100%.
    """
    nu = dash.no_update
    no_op = (nu,) * 8
    if not _portfolio_is_complete(assets, weights):
        return no_op
    if not (_valid_mc_date(fd) and _valid_mc_date(ld)):
        return no_op

    trigger = dash.ctx.triggered_id
    if trigger == "pf-mc-t-var-level":
        if distribution != "t" or var_level in (None, ""):
            return no_op
        start = time.perf_counter()
        try:
            pf = _build_ror_portfolio(assets, weights, ccy, fd, ld, rebal, abs_dev, rel_dev)
            pf.dcf.mc.distribution = "t"
            df = round(float(pf.dcf.mc.optimize_df_for_students(int(var_level))), 6)
        except Exception as e:
            logging.exception("Optimize df failed")
            return nu, nu, nu, nu, nu, nu, nu, f"Could not optimize df: {e}"
        elapsed = time.perf_counter() - start
        logging.info(f"MC df optimization took {elapsed:.3f} s")
        return nu, nu, nu, nu, df, nu, nu, f"df optimized in {elapsed:.2f} s"

    start = time.perf_counter()
    try:
        pf = _build_ror_portfolio(assets, weights, ccy, fd, ld, rebal, abs_dev, rel_dev)
        pf.dcf.mc.distribution = distribution
        params = tuple(round(float(p), 6) for p in pf.dcf.mc.get_parameters_for_distribution())
    except Exception as e:
        logging.exception("Estimate parameters failed")
        return nu, nu, nu, nu, nu, nu, nu, f"Could not estimate: {e}"
    elapsed = time.perf_counter() - start
    logging.info(f"MC parameter estimation took {elapsed:.3f} s")
    message = f"estimated in {elapsed:.2f} s"
    if distribution == "norm":
        mu, sigma = params
        return mu, sigma, nu, nu, nu, nu, nu, message
    if distribution == "lognorm":
        shape, _loc, scale = params
        return nu, nu, shape, scale, nu, nu, nu, message
    if distribution == "t":
        df, loc, scale = params
        return nu, nu, nu, nu, df, loc, scale, message
    return no_op


def _update_graf_portfolio_inner(
    screen, log_on, assets, weights, ccy, rebalancing_period,
    rebal_abs_deviation, rebal_rel_deviation, fd_value, ld_value,
    initial_amount, discount_rate, symbol, cf_strategy, cf_frequency,
    cf_amount, cf_indexation, cf_percentage,
    vds_percentage, vds_min_withdrawal, vds_max_withdrawal, vds_adjust_minmax,
    vds_floor, vds_ceiling, vds_adjust_fc, vds_indexation,
    cwd_amount, cwd_indexation, cwd_thresholds, cwd_reductions,
    ts_dates, ts_amounts,
    plot_type, inflation_on, rolling_window,
    n_monte_carlo, years_monte_carlo, distribution_monte_carlo, show_backtest,
    distribution_parameters_monte_carlo=None,
):
    assets = [i for i in assets if i is not None]
    weights = [i / 100.0 for i in weights if i is not None]
    symbol = symbol.replace(" ", "_")
    symbol = symbol + ".PF" if not symbol.lower().endswith(".pf") else symbol

    abs_dev_val = float(rebal_abs_deviation) / 100 if rebal_abs_deviation else None
    rel_dev_val = float(rebal_rel_deviation) / 100 if rebal_rel_deviation else None

    cf_hash = common.create_link.compute_cashflow_hash(
        cf_strategy=cf_strategy,
        cf_freq=cf_frequency,
        cf_amount=cf_amount,
        cf_indexation=cf_indexation,
        cf_percentage=cf_percentage,
        vds_percentage=vds_percentage,
        vds_min_withdrawal=vds_min_withdrawal,
        vds_max_withdrawal=vds_max_withdrawal,
        vds_adjust_minmax=vds_adjust_minmax,
        vds_floor=vds_floor,
        vds_ceiling=vds_ceiling,
        vds_adjust_fc=vds_adjust_fc,
        vds_indexation=vds_indexation,
        cwd_amount=cwd_amount,
        cwd_indexation=cwd_indexation,
        cwd_thresholds=tuple(cwd_thresholds) if cwd_thresholds else None,
        cwd_reductions=tuple(cwd_reductions) if cwd_reductions else None,
        ts_dates=tuple(ts_dates) if ts_dates else None,
        ts_amounts=tuple(ts_amounts) if ts_amounts else None,
    )
    def _construct_portfolio():
        rebal_strategy = ok.Rebalance(
            period=rebalancing_period,
            abs_deviation=abs_dev_val,
            rel_deviation=rel_dev_val,
        )
        pf = ok.Portfolio(
            assets=assets,
            weights=weights,
            first_date=fd_value,
            last_date=ld_value,
            ccy=ccy,
            rebalancing_strategy=rebal_strategy,
            inflation=inflation_on,
            symbol=symbol,
        )
        pf.dcf.use_discounted_values = True
        pf.dcf.discount_rate = _resolve_discount_rate(discount_rate)
        pf.dcf.cashflow_parameters = _build_cashflow_strategy(
            pf_object=pf,
            strategy_type=cf_strategy,
            frequency=cf_frequency,
            initial_amount=float(initial_amount),
            cf_amount=cf_amount,
            cf_indexation=cf_indexation,
            cf_percentage=cf_percentage,
            vds_percentage=vds_percentage,
            vds_min_withdrawal=vds_min_withdrawal,
            vds_max_withdrawal=vds_max_withdrawal,
            vds_adjust_minmax=vds_adjust_minmax,
            vds_floor=vds_floor,
            vds_ceiling=vds_ceiling,
            vds_adjust_fc=vds_adjust_fc,
            vds_indexation=vds_indexation,
            cwd_amount=cwd_amount,
            cwd_indexation=cwd_indexation,
            cwd_thresholds=cwd_thresholds,
            cwd_reductions=cwd_reductions,
            ts_dates=ts_dates,
            ts_amounts=ts_amounts,
            has_inflation=inflation_on,
        )
        return pf

    pf_object, _ = get_or_create(
        obj_type="portfolio",
        constructor_fn=_construct_portfolio,
        cache_key_params={
            "symbols": assets,
            "weights": weights,
            "ccy": ccy,
            "first_date": fd_value,
            "last_date": ld_value,
            "inflation": inflation_on,
            "rebal": rebalancing_period,
            "abs_dev": rebal_abs_deviation,
            "rel_dev": rebal_rel_deviation,
            "initial_amount": initial_amount,
            "discount_rate": discount_rate,
            "cf_strategy": cf_strategy,
            "cf_freq": cf_frequency,
            "cashflow_hash": cf_hash,
        },
        ttl_seconds=TTL_PORTFOLIO,
    )

    fig, df_backtest, df_forecast, df_data = get_pf_figure(
        pf_object,
        plot_type,
        inflation_on,
        rolling_window,
        n_monte_carlo,
        years_monte_carlo,
        distribution_monte_carlo,
        show_backtest,
        log_on,
        cf_strategy,
        distribution_parameters_monte_carlo=distribution_parameters_monte_carlo,
    )
    json_data = df_data.to_json(orient="split", default_handler=str)
    if plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Indexes")
    elif plot_type in {"cagr", "real_cagr"}:
        fig.update_yaxes(title_text="CAGR")
    elif plot_type == "drawdowns":
        fig.update_yaxes(title_text="Drawdowns")
    elif plot_type == "annual_return":
        fig.update_yaxes(title_text="Annual Return, %")
    elif plot_type == "distribution":
        fig.update_yaxes(title_text="Probability")
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    # PF statistics
    if plot_type == "distribution":
        statistics_dash_table = get_statistics_for_distribution(pf_object)
    else:
        statistics_dash_table = get_pf_statistics_table(pf_object)
    # Monte Carlo statistics
    if n_monte_carlo != 0 and plot_type == "wealth":
        forecast_survival_statistics_datatable = get_forecast_survival_statistics_table(
            df_forecast, df_backtest, pf_object
        )
        forecast_wealth_statistics_datatable = get_forecast_wealth_statistics_table(pf_object)
    else:
        forecast_survival_statistics_datatable = dash_table.DataTable()
        forecast_wealth_statistics_datatable = dash_table.DataTable()
    return fig, config, statistics_dash_table, forecast_survival_statistics_datatable, forecast_wealth_statistics_datatable, json_data


def _resolve_indexation(indexation_value, has_inflation=True):
    if indexation_value is not None:
        return float(indexation_value) / 100
    return "inflation" if has_inflation else 0


def _resolve_discount_rate(discount_rate):
    if discount_rate is None:
        return None
    return float(discount_rate) / 100


def validate_cwd_thresholds(
    cwd_thresholds: list | None,
    cwd_reductions: list | None,
) -> str | None:
    if not cwd_thresholds or not cwd_reductions:
        return "CWD requires at least one complete threshold pair."
    has_complete = False
    for thresh, reduc in zip(cwd_thresholds, cwd_reductions, strict=False):
        t_set = thresh is not None
        r_set = reduc is not None
        if t_set and r_set:
            has_complete = True
        elif t_set or r_set:
            return "Incomplete CWD threshold row: both Drawdown threshold (%) and Reduction (%) must be filled."
    if not has_complete:
        return "CWD requires at least one complete threshold pair."
    complete = [
        (float(thresh), float(reduc))
        for thresh, reduc in zip(cwd_thresholds, cwd_reductions, strict=False)
        if thresh is not None and reduc is not None
    ]
    for i in range(1, len(complete)):
        if complete[i][0] <= complete[i - 1][0] or complete[i][1] <= complete[i - 1][1]:
            return "Drawdown threshold (%) and Reduction (%) must strictly increase with each row."
    return None


def _build_cashflow_strategy(
    pf_object,
    strategy_type,
    frequency,
    initial_amount,
    cf_amount,
    cf_indexation,
    cf_percentage,
    vds_percentage,
    vds_min_withdrawal,
    vds_max_withdrawal,
    vds_adjust_minmax,
    vds_floor,
    vds_ceiling,
    vds_adjust_fc,
    vds_indexation,
    cwd_amount,
    cwd_indexation,
    cwd_thresholds,
    cwd_reductions,
    ts_dates,
    ts_amounts,
    has_inflation=True,
):
    if strategy_type == "percentage":
        s = ok.PercentageStrategy(pf_object)
        s.initial_investment = initial_amount
        s.frequency = frequency
        s.percentage = float(cf_percentage) / 100 if cf_percentage else 0.0
        return s

    if strategy_type == "time_series":
        ts_dict = {}
        if ts_dates and ts_amounts:
            for d, a in zip(ts_dates, ts_amounts):
                if d and a is not None:
                    try:
                        pd.to_datetime(str(d), format="%Y-%m")
                        ts_dict[str(d)] = float(a)
                    except (ValueError, TypeError):
                        pass
        s = ok.TimeSeriesStrategy(pf_object)
        s.initial_investment = initial_amount
        if ts_dict:
            s.time_series_dic = ts_dict
        return s

    if strategy_type == "vds":
        indexation = _resolve_indexation(vds_indexation, has_inflation)
        min_max = None
        if vds_min_withdrawal is not None and vds_max_withdrawal is not None:
            min_max = (float(vds_min_withdrawal), float(vds_max_withdrawal))
        fc = None
        if vds_floor is not None and vds_ceiling is not None:
            fc = (float(vds_floor) / 100, float(vds_ceiling) / 100)
        s = ok.VanguardDynamicSpending(
            parent=pf_object,
            initial_investment=initial_amount,
            percentage=float(vds_percentage) / 100 if vds_percentage else 0.0,
            min_max_annual_withdrawals=min_max,
            adjust_min_max=bool(vds_adjust_minmax),
            floor_ceiling=fc,
            adjust_floor_ceiling=bool(vds_adjust_fc),
            indexation=indexation,
        )
        return s

    if strategy_type == "cwd":
        error = validate_cwd_thresholds(cwd_thresholds, cwd_reductions)
        if error:
            raise ValueError(error)
        indexation = _resolve_indexation(cwd_indexation, has_inflation)
        thresholds = [
            (float(thresh) / 100, float(reduc) / 100)
            for thresh, reduc in zip(cwd_thresholds, cwd_reductions, strict=False)
            if thresh is not None and reduc is not None
        ]
        s = ok.CutWithdrawalsIfDrawdown(
            parent=pf_object,
            initial_investment=initial_amount,
            frequency=frequency,
            amount=float(cwd_amount) if cwd_amount else 0.0,
            indexation=indexation,
            crash_threshold_reduction=thresholds,
        )
        return s

    # Default: IndexationStrategy
    indexation = _resolve_indexation(cf_indexation, has_inflation)
    s = ok.IndexationStrategy(pf_object)
    s.initial_investment = initial_amount
    s.amount = float(cf_amount) if cf_amount else 0.0
    s.frequency = frequency
    s.indexation = indexation
    return s


def get_statistics_for_distribution(pf_object: ok.Portfolio) -> html.Div:
    data = pf_object.ror.dropna()
    mu, std = norm.fit(data)
    df_t, loc_t, scale_t = t.fit(data)
    std_ln, loc_ln, scale_ln = lognorm.fit(data)

    ks_norm = kstest(data, "norm", args=(mu, std))
    ks_lognorm = kstest(data, "lognorm", args=(std_ln, loc_ln, scale_ln))
    ks_t = kstest(data, "t", args=(df_t, loc_t, scale_t))
    jb_stat, jb_pvalue = jarque_bera(data)

    table_list = [
        {"distribution": "Normal", "statistics": ks_norm.statistic, "p-value": ks_norm.pvalue},
        {"distribution": "Lognormal", "statistics": ks_lognorm.statistic, "p-value": ks_lognorm.pvalue},
        {"distribution": "Student's T", "statistics": ks_t.statistic, "p-value": ks_t.pvalue},
    ]
    columns = [
        dict(id="distribution", name="distribution"),
        dict(id="statistics", name="statistics", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
        dict(id="p-value", name="p-value", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
    ]
    statistics_html = html.Div(
        [
            dcc.Markdown(
                """
                **Distribution moments**
                All values correspond to the monthly rate of return.
                """
            ),
            html.P(f"Mean: {data.mean() * 100:.2f}"),
            html.P(f"Standard deviation: {data.std() * 100:.2f}"),
            html.P(f"Skewness: {skew(data):.2f}"),
            html.P(f"Kurtosis: {scipy_kurtosis(data):.2f}"),
            dcc.Markdown(
                """
                **Popular distributions tests**
                """
            ),
            html.P(f"Jarque-Bera test statistic: {jb_stat:.2f}, p-value: {jb_pvalue:.2f}"),
            dcc.Markdown(
                """
                **Kolmogorov-Smirnov test**
                """
            ),
            html.Div(
                [
                    dash_table.DataTable(
                        data=table_list,
                        columns=columns,
                        style_data={"whiteSpace": "normal", "height": "auto", "overflowX": "auto"},
                    )
                ],
            ),
        ]
    )
    return statistics_html


def get_forecast_survival_statistics_table(df_forecast, df_backtsest, pf_object: ok.Portfolio) -> dash_table.DataTable:
    if not df_forecast.empty:
        backtest_survival_period = 0 if df_backtsest.empty else pf_object.dcf.survival_period_hist()
        fsp = pf_object.dcf.monte_carlo_survival_period(threshold=0)
        fsp += backtest_survival_period
        table_list = [
            {"1": "1st percentile", "2": fsp.quantile(1 / 100), "3": "Min", "4": fsp.min()},
            {"1": "5th percentile", "2": fsp.quantile(5 / 100), "3": "Max", "4": fsp.max()},
            {"1": "25th percentile", "2": fsp.quantile(25 / 100), "3": "Mean", "4": fsp.mean()},
            {"1": "50th percentile", "2": fsp.quantile(50 / 100), "3": "Std", "4": fsp.std()},
            {"1": "75th percentile", "2": fsp.quantile(75 / 100), "3": "-", "4": None},
            {"1": "95th percentile", "2": fsp.quantile(95 / 100), "3": "-", "4": None},
            {"1": "99th percentile", "2": fsp.quantile(99 / 100), "3": "-", "4": None},
        ]
        columns = [
            dict(id="1", name="1"),
            dict(id="2", name="2", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
            dict(id="3", name="3"),
            dict(id="4", name="4", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
        ]
        forecast_survival_statistics_datatable = dash_table.DataTable(
            data=table_list,
            columns=columns,
            style_data={"whiteSpace": "normal", "height": "auto", "overflowX": "auto"},
            style_header={"display": "none"},
            export_format="xlsx",
        )
    else:
        backtest_survival_period = pf_object.dcf.survival_period_hist()
        table_list = [{"1": "Backtest survival period", "2": backtest_survival_period}]
        columns = [
            dict(id="1", name="1"),
            dict(id="2", name="2", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
        ]
        forecast_survival_statistics_datatable = dash_table.DataTable(
            data=table_list,
            columns=columns,
            style_data={"whiteSpace": "normal", "height": "auto", "overflowX": "auto"},
            style_header={"display": "none"},
        )
    return forecast_survival_statistics_datatable


def get_forecast_wealth_statistics_table(pf_object) -> dash_table.DataTable:
    wealth_fv = pf_object.dcf.monte_carlo_wealth(discounting="fv")
    if not wealth_fv.empty:
        wealth = wealth_fv.iloc[-1, :]
        wealth_pv = pf_object.dcf.monte_carlo_wealth(discounting="pv").iloc[-1, :]

        rate = f"{pf_object.dcf.discount_rate * 100:.2f}%"
        table_list = [
            {"1": "1st percentile", "2": wealth.quantile(1 / 100), "3": wealth_pv.quantile(1 / 100), "4": "Min", "5": wealth.min(), "6": wealth_pv.min()},
            {"1": "5th percentile", "2": wealth.quantile(5 / 100), "3": wealth_pv.quantile(5 / 100), "4": "Max", "5": wealth.max(), "6": wealth_pv.max()},
            {"1": "25th percentile", "2": wealth.quantile(25 / 100), "3": wealth_pv.quantile(25 / 100), "4": "Mean", "5": wealth.mean(), "6": wealth_pv.mean()},
            {"1": "50th percentile", "2": wealth.quantile(50 / 100), "3": wealth_pv.quantile(50 / 100), "4": "Std", "5": wealth.std(),"6": wealth_pv.std()},
            {"1": "75th percentile", "2": wealth.quantile(75 / 100), "3": wealth_pv.quantile(75 / 100), "4": "Discount rate", "5": None, "6": rate},
            {"1": "95th percentile", "2": wealth.quantile(95 / 100), "3": wealth_pv.quantile(95 / 100), "4": "-", "5": None, "6": None},
            {"1": "99th percentile", "2": wealth.quantile(99 / 100), "3": wealth_pv.quantile(99 / 100), "4": "-", "5": None, "6": None},
        ]
        columns = [
            dict(id="1", name=""),
            dict(id="2", name="FV", type="numeric", format=Format(scheme=Scheme.decimal_integer, group=True)),
            dict(id="3", name="PV", type="numeric", format=Format(scheme=Scheme.decimal_integer, group=True)),
            dict(id="4", name=""),
            dict(id="5", name="FV", type="numeric", format=Format(scheme=Scheme.decimal_integer, group=True)),
            dict(id="6", name="PV", type="numeric", format=Format(scheme=Scheme.decimal_integer, group=True)),
        ]
        forecast_wealth_statistics_datatable = dash_table.DataTable(
            data=table_list,
            columns=columns,
            style_data={"whiteSpace": "normal", "height": "auto", "overflowX": "auto"},
            export_format="xlsx",
            style_header={
                # "display": "none",
                'textAlign': 'center',
                'fontWeight': 'bold'
            },
            tooltip_header={
                1: None,
                2: 'Future Value (not discounted)',
                3: 'Present Value (discounted)',
                4: None,
                5: 'Future Value (not discounted)',
                6: 'Present Value (discounted)',
            },
        )
    else:
        table_list = [{"1": "Wealth", "2": 0}]
        columns = [
            dict(id="1", name="1"),
            dict(id="2", name="2", type="numeric", format=Format(precision=2, scheme=Scheme.decimal)),
        ]
        forecast_wealth_statistics_datatable = dash_table.DataTable(
            data=table_list,
            columns=columns,
            style_data={"whiteSpace": "normal", "height": "auto", "overflowX": "auto"},
            style_header={"display": "none"},
        )
    return forecast_wealth_statistics_datatable


def get_pf_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-1, :]
    statistics_df = add_sharpe_ratio_row(al_object, statistics_df)

    statistics_dict = statistics_df.to_dict(orient="records")

    columns = [
        dict(id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2))
        for i in statistics_df.columns
    ]
    return dash_table.DataTable(
        data=statistics_dict,
        columns=columns,
        style_table={"overflowX": "auto"},
        export_format="xlsx",
    )



def _nullify_after_first_zero(df: pd.DataFrame, column: str) -> None:
    s = df[column]
    zero_mask = s == 0
    if zero_mask.any():
        first_zero = zero_mask.idxmax()
        df.loc[s.index > first_zero, column] = np.nan


def _get_distribution_figure(pf_object: ok.Portfolio) -> go.Figure:
    data = pf_object.ror
    df_t, loc, scale = t.fit(data)
    mu, std = norm.fit(data)
    std_ln, loc_ln, scale_ln = lognorm.fit(data)
    xmin, xmax = data.min(), data.max()
    x = np.linspace(xmin, xmax, 100)
    bins_number = 50 if data.shape[0] >= 120 else 10
    bin_size = (xmax - xmin) / bins_number
    pdf_df = pd.DataFrame(
        {
            "Student’s t": t.pdf(x, loc=loc, scale=scale, df=df_t) * bin_size,
            "Normal": norm.pdf(x, mu, std) * bin_size,
            "Lognormal": lognorm.pdf(x, std_ln, loc_ln, scale_ln) * bin_size,
        },
        index=x + bin_size / 2,
    )
    fig = px.line(pdf_df)
    fig.add_trace(
        go.Histogram(
            x=data,
            histnorm="probability",
            xbins=go.histogram.XBins(size=bin_size),
            marker=go.histogram.Marker(color="lightgreen"),
            name="Historical distribution",
        )
    )
    fig.update_layout(
        title={"text": "Rate of return distribution", "y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        legend_title="Legend",
    )
    fig.update_xaxes(title_text=None)
    fig.update_yaxes(title_text="Probability")
    return fig


def _get_wealth_data(
    pf_object, has_cashflow, n_monte_carlo, show_backtest_bool, distribution_mc, years_mc,
    distribution_parameters_mc=None,
):
    df_backtest = pd.DataFrame()
    df_forecast = pd.DataFrame()
    if n_monte_carlo == 0:
        df = pf_object.dcf.wealth_index(discounting="fv", include_negative_values=False) if has_cashflow else pf_object.wealth_index_with_assets
        if has_cashflow:
            _nullify_after_first_zero(df, pf_object.symbol)
        return_series = pf_object.get_cumulative_return(real=False)
        return df, df_backtest, df_forecast, return_series

    df_backtest = pf_object.dcf.wealth_index(discounting="fv", include_negative_values=False)[[pf_object.symbol]] if show_backtest_bool else pd.DataFrame()
    if not df_backtest.empty:
        _nullify_after_first_zero(df_backtest, pf_object.symbol)
    initial_investment = pf_object.dcf.cashflow_parameters.initial_investment if hasattr(pf_object.dcf.cashflow_parameters, "initial_investment") else settings.INITIAL_INVESTMENT_DEFAULT
    last_backtest_value = df_backtest.iat[-1, -1] if show_backtest_bool else initial_investment
    if last_backtest_value > 0:
        pf_object.dcf.cashflow_parameters.initial_investment = last_backtest_value
        pf_object.dcf.set_mc_parameters(
            distribution=distribution_mc,
            distribution_parameters=distribution_parameters_mc,
            period=years_mc,
            mc_number=n_monte_carlo,
        )
        df_forecast = pf_object.dcf.monte_carlo_wealth()
        df = pd.concat([df_backtest, df_forecast], axis=0, join="outer", ignore_index=False)
    else:
        df = df_backtest
    return df, df_backtest, df_forecast, None


def _build_timeseries_figure(pf_object, df, plot_type, titles, inflation_on, log_scale, condition_monte_carlo, has_cashflow, return_series):
    ind = df.index.to_timestamp("D")
    condition_plot_inflation = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if condition_plot_inflation and not condition_monte_carlo else df.columns,
        log_y=log_scale if plot_type == "wealth" else False,
        title=titles[plot_type],
        height=800,
    )
    fig.update_traces({"line": {"width": 1}})
    fig.update_traces(
        patch={"line": {"width": 3}, "name": pf_object.symbol}, selector={"legendgroup": pf_object.symbol}
    )
    if condition_plot_inflation and not condition_monte_carlo:
        add_inflation_trace(fig, ind, df)
    add_crisis_rectangles(fig, ind[0], ind[-1])
    fig.update_xaxes(rangeslider_visible=True, showgrid=False, zeroline=False)
    fig.update_yaxes(zeroline=True, zerolinecolor="black", zerolinewidth=1, showgrid=False)
    fig.update_layout(xaxis_title=None, legend_title="Assets")

    if not condition_monte_carlo and not has_cashflow:
        annotations_xy = [(ind[-1], y) for y in df.iloc[-1].to_numpy()]
        annotations_text = list((return_series * 100).map("{:,.2f}%".format))
        add_last_value_annotations(fig, annotations_xy, annotations_text)
    else:
        fig.update_traces(showlegend=False)
    return fig


def get_pf_figure(
    pf_object: ok.Portfolio,
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    n_monte_carlo: int,
    years_monte_carlo: int,
    distribution_monte_carlo: str,
    show_backtest: str,
    log_scale: bool,
    cf_strategy: str = "indexation",
    distribution_parameters_monte_carlo=None,
) -> typing.Tuple[plotly.graph_objects.Figure, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if plot_type == "distribution":
        fig = _get_distribution_figure(pf_object)
        return fig, pd.DataFrame(), pd.DataFrame(), pf_object.ror.to_frame()

    if plot_type == "annual_return":
        df = pf_object.annual_return_ts(return_type="cagr").to_frame() * 100
        ind = df.index.to_timestamp(freq="Y")
        fig = px.bar(df, x=ind, y=df.columns, barmode="group", title="Portfolio Annual Return", height=800)
        fig.update_xaxes(dtick="M12", tickformat="%Y", ticklabelmode="instant")
        fig.update_layout(xaxis_title=None, legend_title="Portfolio")
        add_return_type_annotation(fig)
        return fig, pd.DataFrame(), pd.DataFrame(), df

    titles = {
        "wealth": "Portfolio Wealth Index",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "drawdowns": "Portfolio Drawdowns",
    }
    show_backtest_bool = show_backtest == "yes"
    condition_monte_carlo = plot_type == "wealth" and n_monte_carlo != 0
    has_cashflow = cf_strategy != "indexation" or (
        hasattr(pf_object.dcf.cashflow_parameters, "amount") and pf_object.dcf.cashflow_parameters.amount != 0
    )
    if has_cashflow:
        titles["wealth"] = "Portfolio Wealth Index (with Cash Flow)"

    df_backtest = pd.DataFrame()
    df_forecast = pd.DataFrame()
    return_series = None
    if plot_type == "wealth":
        df, df_backtest, df_forecast, return_series = _get_wealth_data(
            pf_object, has_cashflow, n_monte_carlo, show_backtest_bool, distribution_monte_carlo, years_monte_carlo,
            distribution_parameters_monte_carlo,
        )
    elif plot_type in {"cagr", "real_cagr"}:
        df = pf_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=plot_type != "cagr")
        return_series = df.iloc[-1, :]
    elif plot_type == "drawdowns":
        df = pf_object.drawdowns.to_frame()
        return_series = df.iloc[-1, :]

    fig = _build_timeseries_figure(
        pf_object, df, plot_type, titles, inflation_on, log_scale, condition_monte_carlo, has_cashflow, return_series,
    )
    return fig, df_backtest, df_forecast, df



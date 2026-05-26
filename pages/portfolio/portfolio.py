import typing
import warnings
import pickle
from pathlib import Path

import dash
import plotly
from dash import dash_table, callback, ALL, html, dcc
from dash.dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np
from scipy.stats import t, norm, lognorm

import okama as ok

import common
import common.create_link
import common.settings as settings
from common.mobile_screens import adopt_small_screens
from common.update_style import change_style_for_hidden_row
from pages.portfolio.cards_portfolio.portfolio_controls import card_controls
from pages.portfolio.cards_portfolio.portfolio_description import card_portfolio_description
from pages.portfolio.cards_portfolio.portfolio_info import card_assets_info
from pages.portfolio.cards_portfolio.pf_statistics_table import card_table
from pages.portfolio.cards_portfolio.pf_wealth_indexes_chart import card_graf_portfolio
import common.crisis.crisis_data as cr

warnings.simplefilter(action="ignore", category=FutureWarning)

data_folder = Path(__file__).parent.parent.parent / common.cache_directory

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
    cf_indexation_type=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    vds_indexation_type=None,
    cwd_amount=None,
    cwd_tr=None,
    cwd_indexation_type=None,
    cf_ts=None,
    **kwargs,
):
    page = dbc.Container(
        [
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
                            cf_indexation_type=cf_indexation_type,
                            cf_pct=float(cf_pct) if cf_pct else None,
                            vds_pct=float(vds_pct) if vds_pct else None,
                            vds_min=float(vds_min) if vds_min else None,
                            vds_max=float(vds_max) if vds_max else None,
                            vds_adj_mm=vds_adj_mm != "0" if vds_adj_mm is not None else None,
                            vds_floor=float(vds_floor) if vds_floor else None,
                            vds_ceil=float(vds_ceil) if vds_ceil else None,
                            vds_adj_fc=vds_adj_fc == "1" if vds_adj_fc is not None else None,
                            vds_indexation=float(vds_indexation) if vds_indexation else None,
                            vds_indexation_type=vds_indexation_type,
                            cwd_amount=float(cwd_amount) if cwd_amount else None,
                            cwd_indexation_type=cwd_indexation_type,
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
    State(component_id="pf-cf-indexation-type", component_property="value"),
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
    State(component_id="pf-cf-vds-indexation-type", component_property="value"),
    State(component_id="pf-cf-vds-indexation", component_property="value"),
    # CWD
    State(component_id="pf-cf-cwd-amount", component_property="value"),
    State(component_id="pf-cf-cwd-indexation-type", component_property="value"),
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
    cf_indexation_type: str,
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
    vds_indexation_type: str,
    vds_indexation: float,
    # CWD
    cwd_amount: float,
    cwd_indexation_type: str,
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
):
    trigger = dash.ctx.triggered_id
    if trigger == "pf-logarithmic-scale-switch":
        patched_fig = dash.Patch()
        patched_fig["layout"]["yaxis"]["type"] = "log" if log_on else "linear"
        return (
            patched_fig,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    assets = [i for i in assets if i is not None]
    weights = [i / 100.0 for i in weights if i is not None]
    symbol = symbol.replace(" ", "_")
    symbol = symbol + ".PF" if not symbol.lower().endswith(".pf") else symbol

    abs_dev_val = float(rebal_abs_deviation) / 100 if rebal_abs_deviation else None
    rel_dev_val = float(rebal_rel_deviation) / 100 if rebal_rel_deviation else None

    new_pf_file_name = common.create_link.create_filename(
        tickers_list=assets,
        ccy=ccy,
        first_date=fd_value,
        last_date=ld_value,
        weights_list=weights,
        inflation=inflation_on,
        rebal=rebalancing_period,
        abs_dev=rebal_abs_deviation,
        rel_dev=rebal_rel_deviation,
        initial_amount=initial_amount,
        cf_strategy=cf_strategy,
        cf_freq=cf_frequency,
    )
    new_pf_file = data_folder / new_pf_file_name
    if new_pf_file.is_file():
        with open(new_pf_file, 'rb') as f:
            print("found cached Portfolio file...")
            pf_object = pickle.load(f)
    else:
        rebal_strategy = ok.Rebalance(
            period=rebalancing_period,
            abs_deviation=abs_dev_val,
            rel_deviation=rel_dev_val,
        )
        pf_object = ok.Portfolio(
            assets=assets,
            weights=weights,
            first_date=fd_value,
            last_date=ld_value,
            ccy=ccy,
            rebalancing_strategy=rebal_strategy,
            inflation=inflation_on,
            symbol=symbol,
        )
        pf_object.dcf.use_discounted_values = True
        strategy = _build_cashflow_strategy(
            pf_object=pf_object,
            strategy_type=cf_strategy,
            frequency=cf_frequency,
            initial_amount=float(initial_amount),
            discount_rate=discount_rate,
            cf_amount=cf_amount,
            cf_indexation_type=cf_indexation_type,
            cf_indexation=cf_indexation,
            cf_percentage=cf_percentage,
            vds_percentage=vds_percentage,
            vds_min_withdrawal=vds_min_withdrawal,
            vds_max_withdrawal=vds_max_withdrawal,
            vds_adjust_minmax=vds_adjust_minmax,
            vds_floor=vds_floor,
            vds_ceiling=vds_ceiling,
            vds_adjust_fc=vds_adjust_fc,
            vds_indexation_type=vds_indexation_type,
            vds_indexation=vds_indexation,
            cwd_amount=cwd_amount,
            cwd_indexation_type=cwd_indexation_type,
            cwd_indexation=cwd_indexation,
            cwd_thresholds=cwd_thresholds,
            cwd_reductions=cwd_reductions,
            ts_dates=ts_dates,
            ts_amounts=ts_amounts,
        )
        pf_object.dcf.cashflow_parameters = strategy

        # Cache to pickle file
        pf_file_name = common.create_link.create_filename(
            tickers_list=pf_object.symbols,
            ccy=pf_object.currency,
            first_date=pf_object.first_date.strftime('%Y-%m'),
            last_date=pf_object.last_date.strftime('%Y-%m'),
            weights_list=pf_object.weights,
            inflation=inflation_on,
            rebal=pf_object.rebalancing_strategy.period,
            abs_dev=rebal_abs_deviation,
            rel_dev=rebal_rel_deviation,
            initial_amount=float(initial_amount),
            cf_strategy=cf_strategy,
            cf_freq=cf_frequency,
        )
        data_file = data_folder / pf_file_name
        with open(data_file, 'wb') as f:
            pickle.dump(pf_object, f, protocol=pickle.HIGHEST_PROTOCOL)

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
    )
    json_data = df_data.to_json(orient="split", default_handler=str)
    if plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Indexes")
    elif plot_type in {"cagr", "real_cagr"}:
        fig.update_yaxes(title_text="CAGR")
    elif plot_type == "drawdowns":
        fig.update_yaxes(title_text="Drawdowns")
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


def _resolve_indexation(indexation_type, indexation_value, discount_rate):
    if indexation_type == "inflation":
        return "inflation"
    if indexation_value is not None:
        return float(indexation_value)
    if discount_rate is not None:
        return float(discount_rate)
    return None


def _build_cashflow_strategy(
    pf_object,
    strategy_type,
    frequency,
    initial_amount,
    discount_rate,
    cf_amount,
    cf_indexation_type,
    cf_indexation,
    cf_percentage,
    vds_percentage,
    vds_min_withdrawal,
    vds_max_withdrawal,
    vds_adjust_minmax,
    vds_floor,
    vds_ceiling,
    vds_adjust_fc,
    vds_indexation_type,
    vds_indexation,
    cwd_amount,
    cwd_indexation_type,
    cwd_indexation,
    cwd_thresholds,
    cwd_reductions,
    ts_dates,
    ts_amounts,
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
        indexation = _resolve_indexation(vds_indexation_type, vds_indexation, discount_rate)
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
        indexation = _resolve_indexation(cwd_indexation_type, cwd_indexation, discount_rate)
        thresholds = []
        if cwd_thresholds and cwd_reductions:
            for t, r in zip(cwd_thresholds, cwd_reductions):
                if t is not None and r is not None:
                    thresholds.append((float(t) / 100, float(r) / 100))
        if not thresholds:
            thresholds = [(0.20, 0.40), (0.50, 1.0)]
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
    indexation = _resolve_indexation(cf_indexation_type, cf_indexation, discount_rate)
    s = ok.IndexationStrategy(pf_object)
    s.initial_investment = initial_amount
    s.amount = float(cf_amount) if cf_amount else 0.0
    s.frequency = frequency
    s.indexation = indexation
    return s


def get_statistics_for_distribution(pf_object: ok.Portfolio) -> html.Div:
    ks_norm = pf_object.kstest('norm')
    ks_lognorm = pf_object.kstest('lognorm')
    ks_t = pf_object.kstest('t')
    table_list = [
        {"distribution": "Normal", "statistics": ks_norm['statistic'], "p-value": ks_norm['p-value']},
        {"distribution": "Lognormal", "statistics": ks_lognorm['statistic'], "p-value": ks_norm['p-value']},
        {"distribution": "Student's T", "statistics": ks_t['statistic'], "p-value": ks_t['p-value']},
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
            html.P(f"Mean: {pf_object.ror.mean() * 100:.2f}"),
            html.P(f"Standard deviation: {pf_object.ror.std() * 100:.2f}"),
            html.P(f"Skewness: {pf_object.skewness.iloc[-1]:.2f}"),
            html.P(f"Kurtosis: {pf_object.kurtosis.iloc[-1]:.2f}"),
            dcc.Markdown(
                """
                **Popular distributions tests**  
                """
            ),
            html.P(
                f"Jarque-Bera test statistic: {pf_object.jarque_bera['statistic']:.2f}, p-value: {pf_object.jarque_bera['p-value']:.2f}"),
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
    if not pf_object.dcf.monte_carlo_wealth.empty:
        wealth = pf_object.dcf.monte_carlo_wealth.iloc[-1, :]
        # TODO: return after okama 1.4.5 release
        # wealth_pv = pf_object.dcf.monte_carlo_wealth_pv.iloc[-1, :]
        wealth_df_pv = pd.DataFrame()
        wealth_df = pf_object.dcf.monte_carlo_wealth.copy()
        for n, row in enumerate(wealth_df.iterrows()):
            w = row[1]
            w = w / (1.0 + pf_object.dcf.discount_rate / 12) ** n
            wealth_df_pv = pd.concat([wealth_df_pv, w.to_frame().T], sort=False)
        wealth_pv = wealth_df_pv.iloc[-1, :]

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


def add_sharpe_ratio_row(al_object, statistics_df):
    # add Sharpe ratio
    inflation_ts = al_object.inflation_ts if hasattr(al_object, "inflation") else pd.Series()
    inflation = ok.Frame.get_cagr(inflation_ts) if not inflation_ts.empty else None
    rf_rate = inflation if inflation else settings.RISK_FREE_RATE_DEFAULT
    sh_ratio = al_object.get_sharpe_ratio(rf_return=rf_rate)
    # add row
    row = {al_object.symbol: sh_ratio}
    row.update(
        period=al_object._pl_txt,
        property=f"Sharpe ratio (risk free rate: {rf_rate * 100:.2f})",
    )
    return pd.concat([statistics_df, pd.DataFrame(row, index=[0])], ignore_index=True)


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
) -> typing.Tuple[plotly.graph_objects.Figure, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if plot_type == "distribution":
        data = pf_object.ror
        df_backtest = pd.DataFrame()
        df_forecast = pd.DataFrame()
        # Fit distributions to the data:
        df, loc, scale = t.fit(data)  # Student's T distrbution
        mu, std = norm.fit(data)  # mu - mean value
        std_lognorm, loc_lognorm, scale_lognorm = lognorm.fit(data)
        # set PDF
        xmin, xmax = data.min(), data.max()
        x = np.linspace(xmin, xmax, 100)
        bins_number = 50 if data.shape[0] >= 120 else 10
        bin_size = (xmax - xmin) / bins_number
        p1 = t.pdf(x, loc=loc, scale=scale, df=df) * bin_size
        p2 = norm.pdf(x, mu, std) * bin_size
        p3 = lognorm.pdf(x, std_lognorm, loc_lognorm, scale_lognorm) * bin_size
        df = pd.DataFrame({'Student’s t': p1, 'Normal': p2, 'Lognormal':p3}, index=x + bin_size / 2)
        fig = px.line(df)
        fig.add_trace(
            go.Histogram(
                x=data,
                histnorm='probability',
                xbins=go.histogram.XBins(size=bin_size),
                marker=go.histogram.Marker(color="lightgreen"),
                name="Historical distribution"
            )
        )

        fig.update_layout(
            # Update title font
            title={
                "text": "Rate of return distribution",
                "y": 0.9,  # Sets the y position with respect to `yref`
                "x": 0.5,  # Sets the x position of title with respect to `xref`
                "xanchor": "center",  # Sets the title's horizontal alignment with respect to its x position
                "yanchor": "top",  # Sets the title's vertical alignment with respect to its y position. "
            },
            legend_title="Legend",
        )

        # Add X and Y labels
        fig.update_xaxes(title_text=None)
        fig.update_yaxes(title_text="Probability")
    else:
        titles = {
            "cagr": f"Rolling CAGR (window={rolling_window} years)",
            "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
            "drawdowns": "Portfolio Drawdowns",
        }
        show_backtest_bool = True if show_backtest == "yes" else False
        # Select Plot Type
        condition_monte_carlo = plot_type == "wealth" and n_monte_carlo != 0
        df_backtest = pd.DataFrame()
        df_forecast = pd.DataFrame()
        has_cashflow = cf_strategy != "indexation" or (
            hasattr(pf_object.dcf.cashflow_parameters, "amount") and pf_object.dcf.cashflow_parameters.amount != 0
        )
        titles["wealth"] = "Portfolio Wealth Index (with Cash Flow)" if has_cashflow else "Portfolio Wealth Index"
        if plot_type == "wealth":
            if n_monte_carlo == 0:
                df = pf_object.dcf.wealth_index_fv_with_assets if has_cashflow else pf_object.wealth_index_with_assets
                # TODO: calculate return_series: portfolio + assets
                return_series = pf_object.get_cumulative_return(real=False)
            else:
                df_backtest = pf_object.dcf.wealth_index_fv_with_assets[[pf_object.symbol]] if show_backtest_bool else pd.DataFrame()
                initial_investment = pf_object.dcf.cashflow_parameters.initial_investment if hasattr(pf_object.dcf.cashflow_parameters, "initial_investment") else settings.INITIAL_INVESTMENT_DEFAULT
                last_backtest_value = df_backtest.iat[-1, -1] if show_backtest_bool else initial_investment
                if last_backtest_value > 0:
                    pf_object.dcf.cashflow_parameters.initial_investment = last_backtest_value
                    pf_object.dcf.set_mc_parameters(
                        distribution=distribution_monte_carlo,
                        period=years_monte_carlo,
                        number=n_monte_carlo
                    )
                    df_forecast = pf_object.dcf.monte_carlo_wealth
                    df = pd.concat([df_backtest, df_forecast], axis=0, join="outer", copy="false", ignore_index=False)
                else:
                    df = df_backtest
        elif plot_type in {"cagr", "real_cagr"}:
            real = plot_type != "cagr"
            df = pf_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
            return_series = df.iloc[-1, :]
        elif plot_type == "drawdowns":
            df = pf_object.drawdowns.to_frame()
            return_series = df.iloc[-1, :]

        ind = df.index.to_timestamp("D")
        chart_first_date = ind[0]
        chart_last_date = ind[-1]

        if not condition_monte_carlo and not has_cashflow:
            annotations_xy = [(ind[-1], y) for y in df.iloc[-1].values]
            annotation_series = (return_series * 100).map("{:,.2f}%".format)
            annotations_text = list(annotation_series)

        # inflation must not be in the chart for "Real CAGR"
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
        # Plot Inflation
        if condition_plot_inflation and not condition_monte_carlo:
            fig.add_trace(
                go.Scatter(
                    x=ind,
                    y=df.iloc[:, -1],
                    mode="none",
                    fill="tozeroy",
                    fillcolor="rgba(226,150,65,0.5)",
                    name="Inflation",
                )
            )
        # Plot Financial crisis historical data (sample)
        for crisis in cr.crisis_list:
            if (chart_first_date < crisis.first_date_dt) and (chart_last_date > crisis.last_date_dt):
                fig.add_vrect(
                    x0=crisis.first_date,
                    x1=crisis.last_date,
                    annotation_text=crisis.name,
                    annotation=dict(align="left", valign="top", textangle=-90),
                    fillcolor="red",
                    opacity=0.25,
                    line_width=0,
                )
        # Plot x-axis slider
        fig.update_xaxes(
            # ticks='outside',
            rangeslider_visible=True,
            showgrid=False,
            gridcolor="lightgrey",
            zeroline=False,
            zerolinewidth=2,
            zerolinecolor="black",
        )
        fig.update_yaxes(
            # ticks='outside',
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=1,
            showgrid=False,
            gridcolor="lightgrey",
        )
        fig.update_layout(
            xaxis_title=None,
            legend_title="Assets",
        )

        # plot annotations
        if not condition_monte_carlo and not has_cashflow:
            for point in zip(annotations_xy, annotations_text):
                fig.add_annotation(
                    x=point[0][0],
                    y=point[0][1],
                    text=point[1],
                    showarrow=False,
                    xanchor="left",
                    bgcolor="grey",
                )
        else:
            fig.update_traces(showlegend=False)
    return fig, df_backtest, df_forecast, df


@callback(
    Output(component_id="pf-graf-row", component_property="style"),
    Output(component_id="pf-portfolio-statistics-row", component_property="style"),
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State(component_id="pf-graf-row", component_property="style"),
)
def show_graf_and_portfolio_data_rows(n_clicks, style):
    style = change_style_for_hidden_row(n_clicks, style)
    return style, style

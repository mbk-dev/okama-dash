import typing
import warnings

import dash
import plotly
from dash import dash_table, callback, ALL
from dash.dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd

import okama as ok

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

dash.register_page(
    __name__,
    path="/portfolio",
    title="Investment Portfolio : okama",
    name="Investment Portfolio",
    suppress_callback_exceptions=True,
    description="Okama.io widget for Investment Portfolio analysis",
)


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
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    State(component_id="pf-base-currency", component_property="value"),
    State(component_id="pf-rebalancing-period", component_property="value"),
    State(component_id="pf-first-date", component_property="value"),
    State(component_id="pf-last-date", component_property="value"),
    # advanced parameters
    State(component_id="pf-initial-amount", component_property="value"),
    State(component_id="pf-cashflow", component_property="value"),
    State(component_id="pf-discount-rate", component_property="value"),
    State(component_id="pf-ticker", component_property="value"),
    # options
    State(component_id="pf-plot-option", component_property="value"),
    State(component_id="pf-inflation-switch", component_property="value"),
    State(component_id="pf-rolling-window", component_property="value"),
    # monte carlo
    State(component_id="pf-monte-carlo-number", component_property="value"),
    State(component_id="pf-monte-carlo-years", component_property="value"),
    State(component_id="pf-monte-carlo-distribution", component_property="value"),
    State(component_id="pf-monte-carlo-backtest", component_property="value"),
    # Logarithmic scale button
    Input(component_id="pf-logarithmic-scale-switch", component_property="on"),
    prevent_initial_call=True,
)
def update_graf_portfolio(
    screen,
    n_clicks,
    assets: list,
    weights: list,
    ccy: str,
    rebalancing_period: str,
    fd_value: str,
    ld_value: str,
    # Advanced parameters
    initial_amount: float,
    cashflow: float,
    discount_rate: float,
    symbol: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    # Monte Carlo
    n_monte_carlo: int,
    years_monte_carlo: int,
    distribution_monte_carlo: str,
    show_backtest: str,
    # Log scale
    log_on: bool,
):
    assets = [i for i in assets if i is not None]
    weights = [i / 100.0 for i in weights if i is not None]
    symbol = symbol.replace(" ", "_")
    symbol = symbol + ".PF" if not symbol.lower().endswith(".pf") else symbol
    pf_object = ok.Portfolio(
        assets=assets,
        weights=weights,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        rebalancing_period=rebalancing_period,
        inflation=inflation_on,
        # advanced
        initial_amount=initial_amount,
        cashflow=cashflow,
        discount_rate=discount_rate if discount_rate else None,
        symbol=symbol,
    )
    fig, df_backtest, df_forecast = get_pf_figure(
        pf_object,
        plot_type,
        inflation_on,
        rolling_window,
        n_monte_carlo,
        years_monte_carlo,
        distribution_monte_carlo,
        show_backtest,
        log_on,
    )
    if plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Indexes")
    elif plot_type in {"cagr", "real_cagr"}:
        fig.update_yaxes(title_text="CAGR")
    else:
        fig.update_yaxes(title_text="Drawdowns")
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    # PF statistics
    statistics_dash_table = get_pf_statistics_table(pf_object)
    # Monte Carlo statistics
    if n_monte_carlo != 0 and plot_type == "wealth":
        forecast_survival_statistics_datatable = get_forecast_survival_statistics_table(
            df_forecast, df_backtest, pf_object
        )
    else:
        forecast_survival_statistics_datatable = dash_table.DataTable()
    return (fig, config, statistics_dash_table, forecast_survival_statistics_datatable)


def get_forecast_survival_statistics_table(df_forecast, df_backtsest, pf_object) -> dash_table.DataTable:
    # TODO: add survival period of backtest to forecasted survival period
    if not df_forecast.empty:
        backtest_survival_period = 0 if df_backtsest.empty else pf_object.dcf.survival_period
        forecast_dates: pd.Series = ok.Frame.get_survival_date(df_forecast)
        fsp = forecast_dates.apply(ok.Date.get_period_length, args=(pf_object.last_date,))
        fsp += backtest_survival_period
        table_list = [
            {"1": "1st percentile", "2": fsp.quantile(1 / 100), "3": "Min", "4": fsp.min()},
            {"1": "50th percentile", "2": fsp.quantile(50 / 100), "3": "Max", "4": fsp.max()},
            {"1": "99th percentile", "2": fsp.quantile(99 / 100), "3": "Mean", "4": fsp.mean()},
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
        )
    else:
        backtest_survival_period = pf_object.dcf.survival_period
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


def get_pf_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-1, :]
    statistics_dict = statistics_df.to_dict(orient="records")

    columns = [
        dict(id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2))
        for i in statistics_df.columns
    ]
    return dash_table.DataTable(
        data=statistics_dict,
        columns=columns,
        style_table={"overflowX": "auto"},
    )


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
) -> typing.Tuple[plotly.graph_objects.Figure, pd.DataFrame, pd.DataFrame]:
    titles = {
        "wealth": "Portfolio Wealth index",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "drawdowns": "Portfolio Drawdowns",
    }
    show_backtest_bool = True if show_backtest == "yes" else False
    # Select Plot Type
    condition_monte_carlo = plot_type == "wealth" and n_monte_carlo != 0
    df_backtest = pd.DataFrame()
    df_forecast = pd.DataFrame()
    if plot_type == "wealth":
        if n_monte_carlo == 0:
            df = pf_object.wealth_index_with_assets if pf_object.cashflow == 0 else pf_object.dcf.wealth_index
            return_series = pf_object.get_cumulative_return(real=inflation_on)
        else:
            df_backtest = pf_object.dcf.wealth_index[[pf_object.symbol]] if show_backtest_bool else pd.DataFrame()
            last_backtest_value = df_backtest.iat[-1, -1] if show_backtest_bool else pf_object.initial_amount
            if last_backtest_value > 0:
                df_forecast = pf_object.dcf._monte_carlo_wealth(
                    first_value=last_backtest_value,
                    distr=distribution_monte_carlo,
                    years=years_monte_carlo,
                    n=n_monte_carlo,
                )
                df = pd.concat([df_backtest, df_forecast], axis=0, join="outer", copy="false", ignore_index=False)
            else:
                df = df_backtest
    elif plot_type in {"cagr", "real_cagr"}:
        real = plot_type != "cagr"
        df = pf_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
        return_series = df.iloc[-1, :]
    else:
        df = pf_object.drawdowns.to_frame()
        return_series = df.iloc[-1, :]

    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]

    if not condition_monte_carlo and pf_object.cashflow == 0:
        annotations_xy = [(ind[-1], y) for y in df.iloc[-1].values]
        annotation_series = (return_series * 100).map("{:,.2f}%".format)
        annotations_text = list(annotation_series)

    # inflation must not be in the chart for "Real CAGR"
    condition_plot_inflation = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if condition_plot_inflation and not condition_monte_carlo else df.columns,
        log_y=log_scale,
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
        xaxis_title="Date",
        legend_title="Assets",
    )

    # plot annotations
    if not condition_monte_carlo and pf_object.cashflow == 0:
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
    return fig, df_backtest, df_forecast


@callback(
    Output(component_id="pf-graf-row", component_property="style"),
    Output(component_id="pf-portfolio-statistics-row", component_property="style"),
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State(component_id="pf-graf-row", component_property="style"),
)
def show_graf_and_portfolio_data_rows(n_clicks, style):
    style = change_style_for_hidden_row(n_clicks, style)
    return style, style

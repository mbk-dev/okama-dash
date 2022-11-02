import warnings

import dash
from dash import callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import okama as ok

import common.settings as settings
from common.mobile_screens import adopt_small_screens
from pages.benchmark.cards_benchmark.benchmark_chart import card_graf_benchmark
from pages.benchmark.cards_benchmark.benchmark_controls import card_controls

from pages.benchmark.cards_benchmark.benchmark_description import card_benchmark_description
from pages.benchmark.cards_benchmark.benchmark_info import card_benchmark_info

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/benchmark",
    title="Compare with benchmark : okama",
    name="Compare with benchmark",
    description="Okama widget to compare assets with benchmark: tracking difference, tracking error, correlation, beta",
)


def layout(benchmark=None, tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(benchmark, tickers, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_benchmark_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_benchmark, width=12), align="center"),
            dbc.Row(dbc.Col(card_benchmark_description, width=12), align="left"),
        ],
        class_name="mt-2 gap-3",
        fluid="md",
    )
    return page


@callback(
    Output("benchmark-graph", "figure"),
    Output("benchmark-graph", "config"),
    # user screen info
    Input("store", "data"),
    # main Inputs
    Input("benchmark-submit-button", "n_clicks"),
    State("select-benchmark", "value"),
    State("benchmark-assets-list", "value"),
    State("benchmark-base-currency", "value"),
    State("benchmark-first-date", "value"),
    State("benchmark-last-date", "value"),
    # Options
    State("benchmark-plot-option", "value"),
    State("benchmark-rolling-window", "value"),
    prevent_initial_call=True,
)
def update_graf_benchmark(
    screen,
    n_clicks,
    benchmark: str,
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
    # Log scale
    log_on: bool,
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    al_object = ok.AssetList(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=inflation_on,
    )
    fig = get_benchmark_figure(al_object, plot_type, inflation_on, rolling_window, log_on)
    if plot_type == "correlation":
        fig.update(layout_showlegend=False)
        fig.update(layout_coloraxis_showscale=False)
    elif plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Index")
    else:
        fig.update_yaxes(title_text="CAGR")
    # Change layout for mobile screens (except correlation matrix)
    fig, config = adopt_small_screens(fig, screen)
    return fig, config


def get_benchmark_figure(al_object: ok.AssetList, plot_type: str, inflation_on: bool, rolling_window: int, log_scale: bool):
    titles = {
        "wealth": "Assets Wealth indexes",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "correlation": "Correlation Matrix",
    }

    # Select Plot Type
    if plot_type == "wealth":
        df = al_object.wealth_indexes
    elif plot_type in ("cagr", "real_cagr"):
        real = False if plot_type == "cagr" else True
        df = al_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
    elif plot_type == "correlation":
        matrix = al_object.assets_ror.corr()
        matrix = matrix.applymap("{:,.2f}".format)
        fig = px.imshow(matrix, text_auto=True, aspect="equal", labels=dict(x="", y="", color=""))
        return fig

    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]
    # inflation must not be in the chart for "Real CAGR"
    plot_inflation_condition = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if plot_inflation_condition else df.columns,
        log_y=log_scale,
        title=titles[plot_type],
        # width=800,
        height=800,
    )
    # Plot Inflation
    if plot_inflation_condition:
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
    # Plot x-axis slider
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        xaxis_title="Date",
        legend_title="Assets",
    )
    return fig

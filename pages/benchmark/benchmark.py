import warnings

import dash
from dash import callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px

import okama as ok

import common.settings as settings
from common.mobile_screens import adopt_small_screens
from pages.benchmark.cards_benchmark.benchmark_chart import card_graf_benchmark
from pages.benchmark.cards_benchmark.benchmark_controls import benchmark_card_controls

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
                    dbc.Col(benchmark_card_controls(benchmark, tickers, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_benchmark_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_benchmark, width=12), align="center"),
            dbc.Row(dbc.Col(card_benchmark_description, width=12), align="left"),
        ],
        class_name="mt-2",
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
    State("benchmark-chart-expanding-rolling", "value"),
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
    expanding_rolling: str,
    rolling_window: int,
):
    if not selected_symbols or not benchmark:
        raise dash.exceptions.PreventUpdate
    tickers = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    symbols = [benchmark] + tickers
    al_object = ok.AssetList(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=False,
    )
    fig = get_benchmark_figure(al_object, plot_type, expanding_rolling, rolling_window)
    fig, config = adopt_small_screens(fig, screen)
    return fig, config


def get_benchmark_figure(al_object: ok.AssetList, plot_type: str, expanding_rolling: str, rolling_window: int):
    rolling_window = rolling_window * settings.MONTHS_PER_YEAR if expanding_rolling == "rolling" else None
    titles = {
        "td": "Tracking difference",
        "annualized_td": "Annualized tracking difference",
        "annual_td_bar": "Annual tracking difference",
        "te": "Tracking Error",
        "correlation": "Correlation",
        "beta": "Beta coefficient",
    }
    # Select Plot Type
    if plot_type == "td":
        df = al_object.tracking_difference(rolling_window=rolling_window) * 100
    elif plot_type == "annualized_td":
        df = al_object.tracking_difference_annualized(rolling_window=rolling_window) * 100
    elif plot_type == "annual_td_bar":
        df = al_object.tracking_difference_annual * 100
    elif plot_type == "te":
        df = al_object.tracking_error(rolling_window=rolling_window) * 100
    elif plot_type == "correlation":
        df = al_object.index_corr(rolling_window=rolling_window)
    elif plot_type == "beta":
        df = al_object.index_beta(rolling_window=rolling_window)


    if plot_type != "annual_td_bar":
        ind = df.index.to_timestamp("M")
        fig = px.line(
            df,
            x=ind,
            y=df.columns,
            title=titles[plot_type],
            height=800,
        )
        # Plot x-axis slider
        fig.update_xaxes(rangeslider_visible=True)

        return_series = df.iloc[-1, :]

        annotations_xy = [(ind[-1], y) for y in df.iloc[-1].values]
        annotation_series = return_series.map("{:,.2f}%".format) if plot_type not in ("correlation", "beta") else return_series.map("{:,.2f}".format)
        annotations_text = [cum_return for cum_return in annotation_series]

        # plot annotations
        for point in zip(annotations_xy, annotations_text):
            fig.add_annotation(
                x=point[0][0],
                y=point[0][1],
                text=point[1],
                showarrow=False,
                xanchor="left",
                bgcolor="grey",
            )
        fig.update_yaxes(
            # ticks='outside',
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=1,
            showgrid=False,
            gridcolor="lightgrey",
        )
    else:
        ind = df.index.to_timestamp(freq="Y")
        fig = px.bar(df, x=ind, y=df.columns, barmode="relative")
        fig.update_xaxes(dtick="M12", tickformat="%Y", ticklabelmode="instant")

    # X and Y-axis titles
    y_title = get_y_title(plot_type)
    fig.update_yaxes(title_text=y_title)
    fig.update_layout(
        xaxis_title=None,
        legend_title="Assets",
    )
    return fig


def get_y_title(plot_type: str) -> str:
    titles = {
        "td": "Tracking difference, %",
        "annualized_td": "Annualized Tracking difference, %",
        "annual_td_bar": "Annual Tracking difference, %",
        "te": "Tracking Error, %",
        "correlation": "Correlation",
        "beta": "Beta coefficient",
    }
    return titles.get(plot_type)

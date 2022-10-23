import json

import dash
import numpy as np
import okama
from dash import callback, html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.graph_objects as go

import pandas as pd

import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info
from common.parse_query import make_list_from_string
from pages.efficient_frontier.cards_efficient_frontier.ef_info import card_ef_info
from pages.efficient_frontier.cards_efficient_frontier.ef_chart import card_graf
from pages.efficient_frontier.cards_efficient_frontier.ef_controls import card_controls
from common.mobile_screens import adopt_small_screens

dash.register_page(
    __name__,
    path="/",
    title="Efficient Frontier : okama",
    name="Efficient Frontier",
    description="Efficient Frontier for the investment portfolios",
)


def layout(tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    tickers_list = make_list_from_string(tickers)
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers_list, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_ef_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf, width=12), align="center"),
            dbc.Row(
                html.Div(
                    [
                        dcc.Markdown("""
                        **Portfolio data**  
                        Click on points to get portfolio data.
                        """),
                        html.P(id='ef-click-data-risk'),
                        html.P(id='ef-click-data-return'),
                        html.Pre(id='ef-click-data-weights'),
                    ]),
            )
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="ef-graf", component_property="figure"),
    Output(component_id="ef-graf", component_property="config"),
    # Inputs
    Input(component_id="store", component_property="data"),
    # Main input for EF
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef-base-currency", component_property="value"),
    State(component_id="ef-first-date", component_property="value"),
    State(component_id="ef-last-date", component_property="value"),
    # Options
    State(component_id="rate-of-return-options", component_property="value"),
    State(component_id="cml-option", component_property="value"),
    State(component_id="risk-free-rate-option", component_property="value"),
    # Monte-Carlo
    State(component_id="monte-carlo-option", component_property="value"),
    # Input(component_id="ef-return-type-checklist-input", component_property="value"),
    prevent_initial_call=False,
)
def update_ef_cards(
    screen,
    n_clicks,
    # Main input
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    ror_option: str,
    cml_option: str,
    rf_rate: float,
    n_monte_carlo: int,
):
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    ef_object = ok.EfficientFrontier(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=False,
        n_points=40,
        full_frontier=True,
    )
    ef_options = dict(ror=ror_option, cml=cml_option, rf_rate=rf_rate, n_monte_carlo=n_monte_carlo)
    fig = make_ef_figure(ef_object, ef_options)
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    return fig, config


def make_ef_figure(ef_object: okama.EfficientFrontier, ef_options: dict):
    ef = ef_object.ef_points * 100
    # Efficient Frontier
    y_value = ef["Mean return"] if ef_options["ror"] == "Arithmetic" else ef["CAGR"]
    weights_array = np.stack([ef[n] for n in ef.columns[3:]], axis=-1)
    fig = go.Figure(
        data=go.Scatter(
            x=ef["Risk"],
            y=y_value,
            customdata=weights_array,
            hovertemplate=('<b>Risk: %{x:.2f}% <br>Return: %{y:.2}%</b>' +
                           '<extra></extra>'),
            mode="lines",
            name=f"Efficient Frontier - {ef_options['ror']} mean",
        )
    )
    # CML line
    if ef_options["cml"] == "On":
        cagr_option = ef_options["ror"] == "Geometric"
        rf_rate = ef_options["rf_rate"]
        tg = ef_object.get_tangency_portfolio(cagr=cagr_option, rf_return=rf_rate / 100)
        weights_array = np.expand_dims(tg['Weights'], axis=0)
        x_cml, y_cml = [0, tg["Risk"] * 100], [rf_rate, tg["Rate_of_return"] * 100]
        fig.add_trace(
            go.Scatter(
                x=x_cml,
                y=y_cml,
                mode="lines",
                name="Capital Market Line (CML)",
                line=dict(width=0.5, color="green"),
            )
        )
        # Tangency portfolio
        fig.add_trace(
            go.Scatter(
                x=[x_cml[1]],
                y=[y_cml[1]],
                customdata=weights_array,
                hovertemplate='Risk: %{x:.2f}%<br>Return: %{y:.2}%',
                mode="markers+text",
                text="MSR",
                textposition="top left",
                name="Tangency portfolio (MSR)",
                marker=dict(size=8, color="grey"),
            )
        )
    # Assets Risk-Return points
    ror_df = ef_object.mean_return if ef_options["ror"] == "Arithmetic" else ef_object.get_cagr()
    df = pd.concat(
        [ror_df, ef_object.risk_annual],
        axis=1,
        join="outer",
        copy="false",
        ignore_index=False,
    )
    df *= 100
    df.rename(columns={0: "Return", 1: "Risk"}, inplace=True)
    df.reset_index(drop=False, inplace=True)
    fig.add_trace(
        go.Scatter(
            x=df["Risk"],
            y=df["Return"],
            mode="markers+text",
            marker=dict(size=8, color="orange"),
            text=df.iloc[:, 0].to_list(),
            textposition="bottom right",
            name="Assets",
        )
    )
    # Monte-Carlo simulation
    if ef_options["n_monte_carlo"]:
        kind = "mean" if ef_options["ror"] == "Arithmetic" else "cagr"
        df = ef_object.get_monte_carlo(n=ef_options["n_monte_carlo"], kind=kind) * 100
        weights_array = np.stack([df[n] for n in df.columns[2:]], axis=-1)
        fig.add_trace(
            go.Scatter(
                x=df["Risk"],
                y=df["Return"] if ef_options["ror"] == "Arithmetic" else df["CAGR"],
                customdata=weights_array,
                # customdata=weights_array,
                hovertemplate='Risk: %{x:.2f}%<br>Return: %{y:.2}%',
                mode="markers",
                name=f"Monte-Carlo Simulation",
            )
        )
    # X and Y titles
    fig.update_layout(
        height=800,
        xaxis_title="Risk (standard deviation)",
        yaxis_title="Rate of Return",
    )
    return fig


@callback(
    Output('ef-click-data-risk', 'children'),
    Output('ef-click-data-return', 'children'),
    Output('ef-click-data-weights', 'children'),
    Input('ef-graf', 'clickData'))
def display_click_data(clickData):
    if not clickData:
        raise dash.exceptions.PreventUpdate
    risk = clickData["points"][0]["x"]
    rist_str = f"Risk: {risk:.2f}%"

    ror = clickData["points"][0]["y"]
    ror_str = f"Return: {ror:.2f}%"

    weights_str = None
    try:
        weights_list = clickData["points"][0]['customdata']
    except KeyError:
        pass
    else:
        weights_str = "Weights:" + ",".join([f"{x:.2f}% " for x in weights_list])
    return rist_str, ror_str, weights_str

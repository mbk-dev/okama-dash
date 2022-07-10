import dash
from dash import callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.graph_objects as go

import pandas as pd

import okama as ok

from common.assets_names_dash_table import get_assets_names
from pages.cards_efficient_frontier.ef_assets_names import card_assets_info
from pages.cards_efficient_frontier.ef_chart import card_graf
from pages.cards_efficient_frontier.ef_controls import card_controls
from common.mobile_screens import adopt_small_screens

dash.register_page(__name__,
                   path='/',
                   title='Efficient Frontier : okama',
                   name='Efficient Frontier',
                   description="Efficient Frontier for the investment portfolios",
                   )

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(card_controls, lg=7),
                dbc.Col(card_assets_info, lg=5),
            ]
        ),
        dbc.Row(dbc.Col(card_graf, width=12), align="center"),
    ],
    class_name="mt-2",
    fluid="md",
)


@callback(
    Output(component_id="ef-graf", component_property="figure"),
    Output(component_id="ef-graf", component_property="config"),
    Output(component_id="ef-assets-names", component_property="children"),
    Input(component_id="store", component_property="data"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef-base-currency", component_property="value"),
    State(component_id="ef-first-date", component_property="value"),
    State(component_id="ef-last-date", component_property="value"),
    # Input(component_id="ef-return-type-checklist-input", component_property="value"),
)
# @cache.memoize(timeout=86400)
def update_graf(
    screen, n_clicks, selected_symbols: list, ccy: str, fd_value: str, ld_value: str
):
    symbols = (
        selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    )
    ef_object = ok.EfficientFrontier(
        symbols,
        first_date=fd_value, last_date=ld_value,
        ccy=ccy,
        inflation=False,
        n_points=40,
        full_frontier=True
    )
    fig = make_ef_figure(ef_object)
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    # Get assets names
    names_table = get_assets_names(ef_object)
    return fig, config, names_table


def make_ef_figure(ef_object, rf_return: float = 0):
    ef = ef_object.ef_points * 100
    tg = ef_object.get_tangency_portfolio(rf_return)
    x_cml, y_cml = [0, tg["Risk"] * 100], [rf_return, tg["Mean_return"] * 100]
    fig = go.Figure(data=go.Scatter(
        x=ef["Risk"],
        y=ef["Mean return"],
        mode="lines",
        name="Efficient Frontier - arithmetic mean"
    ))
    # CAGR
    fig.add_trace(
        go.Scatter(
            x=ef["Risk"],
            y=ef["CAGR"],
            mode='lines',
            name='Efficient Frontier - geometric mean',
            # line=dict(width=.5, color='green'),
        )
    )
    # CML line
    fig.add_trace(
        go.Scatter(
            x=x_cml,
            y=y_cml,
            mode='lines',
            name='Capital Market Line (CML)',
            line=dict(width=.5, color='green'),
        )
    )
    # Tangency portfolio
    fig.add_trace(
        go.Scatter(
            x=[x_cml[1]],
            y=[y_cml[1]],
            mode='markers+text',
            text="MSR",
            textposition="top left",
            name='Tangency portfolio (MSR)',
            marker=dict(size=8, color="grey"),
        )
    )
    df = pd.concat([ef_object.mean_return, ef_object.risk_annual], axis=1, join="outer", copy="false",
                   ignore_index=False)
    try:
        df.drop([ef_object.inflation], axis=0, inplace=True)
    except:
        pass
    df *= 100
    df.rename(columns={0: "Return", 1: "Risk"}, inplace=True)
    df.reset_index(drop=False, inplace=True)
    fig.add_trace(
        go.Scatter(x=df["Risk"],
                   y=df["Return"],
                   mode='markers+text',
                   marker=dict(size=8, color="orange"),
                   text=df.iloc[:, 0].to_list(),
                   textposition="bottom right",
                   name="Assets"
                   )
    )
    # X and Y titles
    fig.update_layout(
        height=800,
        xaxis_title="Risk (standard deviation)",
        yaxis_title="Rate of Return",
    )
    return fig

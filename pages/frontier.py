import dash
from dash import html, callback, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.graph_objects as go

import pandas as pd

import okama as ok

from application import cache
from application.cards_efficient_frontier.ef_controls import card_controls
from application.cards_efficient_frontier.ef_assets_names import card_assets_info
from application.cards_efficient_frontier.ef_chart import card_graf_compare

dash.register_page(__name__,
                   path='/frontier',
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
        dbc.Row(dbc.Col(card_graf_compare, width=12), align="center"),
    ],
    class_name="mt-2",
    fluid=False,
)


@callback(
    Output(component_id="ef-graf", component_property="figure"),
    Output(component_id="ef-assets-names", component_property="children"),
    Input(component_id="ef-submit-button-state", component_property="n_clicks"),
    State(component_id="ef-symbols-list", component_property="value"),
    State(component_id="ef-base-currency", component_property="value"),
    State(component_id="ef-first-date", component_property="value"),
    State(component_id="ef-last-date", component_property="value"),
)
# @cache.memoize(timeout=86400)
def update_graf(
    n_clicks, selected_symbols: list, ccy: str, fd_value: str, ld_value: str
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
    ef = ef_object.ef_points * 100
    # TODO: insert correct rf_return variable
    rf_return = 0
    tg = ef_object.get_tangency_portfolio(rf_return)
    x_cml, y_cml = [0, tg["Risk"] * 100], [rf_return, tg["Mean_return"] * 100]

    fig = go.Figure(data=go.Scatter(
        x=ef["Risk"],
        y=ef["Mean return"],
        mode="lines",
        name="Efficient Frontier"
    ))
    # fig.update_layout(height=800)
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
    # fig.add_annotation(x=x_cml[1], y=y_cml[1],
    #                    text="MSR",
    #                    showarrow=True,
    #                    arrowhead=1)
    # Assets
    df = pd.concat([ef_object.mean_return, ef_object.risk_annual], axis=1, join="outer", copy="false", ignore_index=False)
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
        yaxis_title="Rate of return (arithmetic mean)",
    )

    # Get assets names
    names_df = (
        pd.DataFrame.from_dict(ef_object.names, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "Ticker", 0: "Long name"})[["Ticker", "Long name"]]
    )
    names_table = dash_table.DataTable(
        data=names_df.to_dict(orient="records"),
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },
        page_size=4,
    )
    return fig, names_table

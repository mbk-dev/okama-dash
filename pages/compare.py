import warnings

import dash
from dash import html, dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import okama as ok

from application import cache
from application.cards_compare.asset_list_controls import card_controls
from application.cards_compare.assets_names import card_assets_info
from application.cards_compare.statistics_table import card_table
from application.cards_compare.wealth_indexes_chart import card_graf_compare

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(__name__,
                   path='/compare',
                   title='Compare financial assets : okama',
                   name='Compare assets',
                   description="Okama widget to compare financial assets properties: rate of return, risk, CVAR, drawdowns",
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
        dbc.Row(dbc.Col(card_table, width=12), align="center"),
    ],
    class_name="mt-2",
    fluid="md",
)


@callback(
    Output(component_id="wealth-indexes", component_property="figure"),
    Output(component_id="assets-names", component_property="children"),
    Output(component_id="describe-table", component_property="children"),
    Input(component_id="submit-button-state", component_property="n_clicks"),
    State(component_id="symbols-list", component_property="value"),
    State(component_id="base-currency", component_property="value"),
    State(component_id="first-date", component_property="value"),
    State(component_id="last-date", component_property="value"),
    Input(component_id="logarithmic-scale-switch", component_property="on"),
)
@cache.memoize(timeout=86400)
def update_graf_compare(
    n_clicks, selected_symbols: list, ccy: str, fd_value: str, ld_value: str, on: bool
):
    symbols = (
        selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    )
    al = ok.AssetList(
        symbols, first_date=fd_value, last_date=ld_value, ccy=ccy, inflation=True
    )
    df = al.wealth_indexes
    ind = df.index.to_timestamp("D")
    statistics_table = al.describe().iloc[
        :-4, :
    ]  # there is a problem with dates '2020-08' in the last 4 rows
    columns = [
        dict(
            id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2)
        )
        for i in statistics_table.columns
    ]
    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1],
        log_y=on,
        title="Assets Wealth indexes",
        # width=800,
        height=800,
    )
    # Plot Inflation
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
    crisis_first_date = pd.to_datetime("2007-10", format="%Y-%m")
    crisis_last_date = pd.to_datetime("2009-09", format="%Y-%m")
    if (al.first_date < crisis_first_date) and (al.last_date > crisis_last_date):
        fig.add_vrect(
            x0=crisis_first_date.strftime(format="%Y-%m"),
            x1=crisis_last_date.strftime(format="%Y-%m"),
            annotation_text="US Housing Bubble",
            annotation_position="top left",
            fillcolor="red",
            opacity=0.25,
            line_width=0,
        )

    # Plot x-axis slider
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        xaxis_title="Date",
        legend_title="Assets",
        # font=dict(
        #     family="Courier New, monospace",
        #     size=18,
        #     color="RebeccaPurple"
        # )
    )

    names_df = (
        pd.DataFrame.from_dict(al.names, orient="index")
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

    statistics_table = dash_table.DataTable(
        data=statistics_table.to_dict(orient="records"),
        columns=columns,
        style_table={"overflowX": "auto"},
    )
    return fig, names_table, statistics_table

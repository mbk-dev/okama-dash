import warnings

import dash
from dash import dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info
from common.mobile_screens import adopt_small_screens
from pages.compare.cards_compare.asset_list_controls import card_controls
from pages.compare.cards_compare.assets_info import card_assets_info
from pages.compare.cards_compare.statistics_table import card_table
from pages.compare.cards_compare.wealth_indexes_chart import card_graf_compare

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/compare",
    title="Compare financial assets : okama",
    name="Compare assets",
    description="Okama widget to compare financial assets properties: rate of return, risk, CVAR, drawdowns",
)


def layout(tickers=None, first_date=None, last_date=None, ccy=None, **kwargs):
    page = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(card_controls(tickers, first_date, last_date, ccy), lg=7),
                    dbc.Col(card_assets_info, lg=5),
                ]
            ),
            dbc.Row(dbc.Col(card_graf_compare, width=12), align="center"),
            dbc.Row(dbc.Col(card_table, width=12), align="center"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="al-wealth-indexes", component_property="figure"),
    Output(component_id="al-wealth-indexes", component_property="config"),
    Output(component_id="al-compare-info", component_property="children"),
    Output(component_id="al-assets-names", component_property="children"),
    Output(component_id="al-describe-table", component_property="children"),
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(
        component_id="al-submit-button", component_property="n_clicks"
    ),  # n_clicks
    State(component_id="al-symbols-list", component_property="value"),
    State(component_id="al-base-currency", component_property="value"),
    State(component_id="al-first-date", component_property="value"),
    State(component_id="al-last-date", component_property="value"),
    # Options
    State(component_id="al-inflation-option", component_property="value"),
    # Logarithmic scale button
    Input(component_id="logarithmic-scale-switch", component_property="on"),
)
def update_graf_compare(
    screen,
    n_clicks,
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    inflation_on: list,
    log_on: bool,
):
    symbols = (
        selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    )
    inflation_on_bool = inflation_on != []
    al_object = ok.AssetList(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=inflation_on_bool,
    )
    fig = get_al_figure(al_object, inflation_on, log_on)
    # Change layout for mobile screens
    fig, config = adopt_small_screens(fig, screen)
    # AL Info
    info_table = get_info(al_object)
    names_table = get_assets_names(al_object)
    # AL statistics
    statistics_dash_table = get_al_statistics_table(al_object)
    return fig, config, info_table, names_table, statistics_dash_table


def get_al_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-4, :]
    # statistics_df = al_object.describe()
    # statistics_df.iloc[-4:, :] = statistics_df.iloc[-4:, :].applymap(str)
    statistics_dict = statistics_df.to_dict(orient="records")

    columns = [
        dict(
            id=i, name=i, type="numeric", format=dash_table.FormatTemplate.percentage(2)
        )
        for i in statistics_df.columns
    ]
    return dash_table.DataTable(
        data=statistics_dict,
        columns=columns,
        style_table={"overflowX": "auto"},
    )


def get_al_figure(al_object, inflation_on, log_scale):
    df = al_object.wealth_indexes
    ind = df.index.to_timestamp("D")
    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if inflation_on else df.columns,
        log_y=log_scale,
        title="Assets Wealth indexes",
        # width=800,
        height=800,
    )
    # Plot Inflation
    if inflation_on:
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
    if (al_object.first_date < crisis_first_date) and (
        al_object.last_date > crisis_last_date
    ):
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
    )
    return fig

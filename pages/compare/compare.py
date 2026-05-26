import typing
import warnings

import dash
import dash.exceptions
import plotly
from dash import dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd

import plotly.express as px

import okama as ok

import common.settings as settings
import common.update_style
from common.chart_helpers import add_inflation_trace, add_crisis_rectangles, add_last_value_annotations, add_sharpe_ratio_row

from common.mobile_screens import adopt_small_screens
from pages.compare.cards_compare.asset_list_controls import card_controls
from pages.compare.cards_compare.assets_info import card_assets_info
from pages.compare.cards_compare.compare_description import card_compare_description
from pages.compare.cards_compare.statistics_table import card_table
from pages.compare.cards_compare.wealth_indexes_chart import card_graf_compare

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/compare",
    title="Compare financial assets : okama",
    name="Compare assets",
    description="""Okama.io widget to compare financial assets properties: 
                rate of return, risk, CVAR, drawdowns, correlation""",
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
            dbc.Row(dbc.Col(card_graf_compare, width=12), align="center", style={"display": "none"}, id="al-graf-row"),
            dbc.Row(
                dbc.Col(card_table, width=12), align="center", style={"display": "none"}, id="al-statistics-table-row"
            ),
            dbc.Row(dbc.Col(card_compare_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page


@callback(
    Output(component_id="al-wealth-indexes", component_property="figure"),
    Output(component_id="al-wealth-indexes", component_property="config"),
    Output(component_id="al-describe-table", component_property="children"),
    Output(component_id="al-store-chart-data", component_property="data"),
    # user screen info
    Input(component_id="store", component_property="data"),
    # main Inputs
    Input(component_id="al-submit-button", component_property="n_clicks"),
    # Logarithmic scale button
    Input(component_id="logarithmic-scale-switch", component_property="on"),
    State(component_id="al-symbols-list", component_property="value"),
    State(component_id="al-base-currency", component_property="value"),
    State(component_id="al-first-date", component_property="value"),
    State(component_id="al-last-date", component_property="value"),
    # Options
    State(component_id="al-plot-option", component_property="value"),
    State(component_id="al-inflation-switch", component_property="value"),
    State(component_id="al-rolling-window", component_property="value"),
    prevent_initial_call=True,
)
def update_graf_compare(
    screen,
    n_clicks,
    log_on: bool,
    selected_symbols: list,
    ccy: str,
    fd_value: str,
    ld_value: str,
    # Options
    plot_type: str,
    inflation_on: bool,
    rolling_window: int,
):
    trigger = dash.ctx.triggered_id
    if trigger == "logarithmic-scale-switch":
        patched_fig = dash.Patch()
        patched_fig["layout"]["yaxis"]["type"] = "log" if log_on else "linear"
        return (
            patched_fig,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    if not selected_symbols:
        raise dash.exceptions.PreventUpdate
    symbols = selected_symbols if isinstance(selected_symbols, list) else [selected_symbols]
    al_object = ok.AssetList(
        symbols,
        first_date=fd_value,
        last_date=ld_value,
        ccy=ccy,
        inflation=inflation_on,
    )
    log_scale = log_on if plot_type == "wealth" else False  # log scale Y must be available only for wealth chart
    fig, df_data = get_al_figure(al_object, plot_type, inflation_on, rolling_window, log_scale)
    json_data = df_data.to_json(orient="split", default_handler=str)
    if plot_type == "correlation":
        fig.update(layout_showlegend=False)
        fig.update(layout_coloraxis_showscale=False)
        fig.update_xaxes(side="top")
    elif plot_type == "wealth":
        fig.update_yaxes(title_text="Wealth Index")
    else:
        fig.update_yaxes(title_text="CAGR")

    # Change layout for mobile screens (except correlation matrix)
    fig, config = adopt_small_screens(fig, screen)
    fig.update_xaxes(
        # ticks='outside',
        rangeslider_visible=False if plot_type == "correlation" else True,
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
    # Asset List describe() risk-return statistics
    statistics_dash_table = get_al_statistics_table(al_object)
    return fig, config, statistics_dash_table, json_data


def get_al_statistics_table(al_object):
    statistics_df = al_object.describe().iloc[:-4, :]  # crop from Max drawdown date
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



def get_al_figure(
        al_object: ok.AssetList,
        plot_type: str,
        inflation_on: bool,
        rolling_window: int,
        log_scale: bool
) -> typing.Tuple[plotly.graph_objects.Figure, pd.DataFrame]:
    titles = {
        "wealth": "Assets Wealth indexes",
        "cagr": f"Rolling CAGR (window={rolling_window} years)",
        "real_cagr": f"Rolling real CAGR (window={rolling_window} years)",
        "correlation": "Correlation Matrix",
    }

    # Select Plot Type
    if plot_type == "wealth":
        df = al_object.wealth_indexes
        return_series = al_object.get_cumulative_return(real=False)
    elif plot_type in ("cagr", "real_cagr"):
        real = False if plot_type == "cagr" else True
        df = al_object.get_rolling_cagr(window=rolling_window * settings.MONTHS_PER_YEAR, real=real)
        return_series = df.iloc[-1, :]
    elif plot_type == "correlation":
        matrix = al_object.assets_ror.corr()
        matrix = matrix.map("{:,.2f}".format)
        fig = px.imshow(matrix, text_auto=True, aspect="equal", labels=dict(x="", y="", color=""))
        return fig, matrix

    ind = df.index.to_timestamp("D")
    chart_first_date = ind[0]
    chart_last_date = ind[-1]

    annotations_xy = [(ind[-1], y) for y in df.iloc[-1].values]
    annotation_series = (return_series * 100).map("{:,.2f}%".format)
    annotations_text = [cum_return for cum_return in annotation_series]

    # inflation must not be in the chart for "Real CAGR"
    plot_inflation_condition = inflation_on and plot_type != "real_cagr"

    fig = px.line(
        df,
        x=ind,
        y=df.columns[:-1] if plot_inflation_condition else df.columns,
        log_y=log_scale if plot_type == "wealth" else False,
        title=titles[plot_type],
        # width=800,
        height=800,
    )
    if plot_inflation_condition:
        add_inflation_trace(fig, ind, df)
    add_crisis_rectangles(fig, chart_first_date, chart_last_date)
    fig.update_layout(
        xaxis_title=None,
        legend_title="Assets",
    )
    add_last_value_annotations(fig, annotations_xy, annotations_text)

    return fig, df


@callback(
    Output(component_id="al-graf-row", component_property="style"),
    Output(component_id="al-statistics-table-row", component_property="style"),
    Input(component_id="al-submit-button", component_property="n_clicks"),
    State(component_id="al-graf-row", component_property="style"),
)
def show_graf_and_statistics_table_rows(n_clicks, style):
    style = common.update_style.change_style_for_hidden_row(n_clicks, style)
    return style, style

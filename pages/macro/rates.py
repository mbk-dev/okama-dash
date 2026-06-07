"""/macro/rates — interest rates in three series groups (Macro section).

A group selector switches between central bank key rates, Russian bank deposit
rates and Russian money-market rates (RUONIA/RUSFAR); switching swaps the
series multiselect options and defaults, and the reactive main callback
recalculates through the series Input (spec section 5.2).
"""

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State

from common.date_input import register_date_validation
from common.html_elements.copy_link_div import create_copy_link_div
from common.html_elements.grid_export import (
    create_grid_header_with_export,
    percent_column_formats,
    rowdata_to_xlsx_download,
)
from common.mobile_screens import adopt_small_screens
from common.parse_query import make_list_from_string
from pages.macro import macro_objects
from pages.macro.cards_macro.eng.rates_description_txt import rates_description_text
from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_controls import (
    date_columns,
    dates_ready,
    make_submit_guard,
    series_multiselect_column,
)
from pages.macro.cards_macro.macro_description import macro_description_card
from pages.macro.cards_macro.macro_stats import build_describe_table, build_stats_grid
from pages.macro.macro_data import (
    ALL_RATES_SERIES,
    MACRO_FIRST_DATE_DEFAULT,
    RATES_GROUPS,
    filter_known,
    rates_group_catalog,
)
from pages.macro.macro_link import build_macro_link

dash.register_page(
    __name__,
    path="/macro/rates",
    title="Key rates : okama",
    name="Rates",
    description=(
        "Okama.io widget: central bank key rates — Bank of Russia, US Fed EFFR, ECB, "
        "Bank of England, Bank of Israel, PBoC LPR"
    ),
)

today_str = pd.Timestamp.today().strftime("%Y-%m")


def get_rates_figure(objects: list) -> go.Figure:
    df = pd.concat([obj.values_monthly for obj in objects], axis=1) * 100
    df.columns = [ALL_RATES_SERIES.get(col, col) for col in df.columns]
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="Interest rates", height=600)
    fig.update_traces(line_shape="hv")  # rates change stepwise
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text="Rate, %", zeroline=True, zerolinecolor="black", zerolinewidth=1)
    fig.update_layout(xaxis_title=None, legend_title="Series")
    return fig


def layout(tickers=None, first_date=None, last_date=None, group=None, **kwargs):
    group_value = group if group in RATES_GROUPS else "key"
    catalog = rates_group_catalog(group_value)
    group_defaults = RATES_GROUPS[group_value][2]
    selected = filter_known(make_list_from_string(tickers), catalog) or group_defaults
    control_bar = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Group"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": label, "value": value}
                                        for value, (label, _, _) in RATES_GROUPS.items()
                                    ],
                                    value=group_value,
                                    clearable=False,
                                    id="rates-group",
                                ),
                            ],
                            lg=2,
                            md=3,
                            sm=6,
                        ),
                        series_multiselect_column("rates", catalog, selected),
                        *date_columns("rates", first_date or MACRO_FIRST_DATE_DEFAULT, last_date or today_str),
                    ],
                    class_name="g-2",
                    # Top-aligned: every column starts with a one-line Label, so
                    # the 38px controls land on one horizontal line.
                    align="start",
                ),
                dbc.Row(
                    create_copy_link_div(
                        location_id="rates-url",
                        hidden_div_with_url_id="rates-show-url",
                        button_id="rates-copy-link-button",
                        card_name="widget",
                    ),
                ),
            ]
        ),
        class_name="mb-3",
    )
    stats_card = dbc.Card(
        dbc.CardBody(
            [
                create_grid_header_with_export("Statistics", "rates-statistics-export-btn"),
                dcc.Download(id="rates-statistics-download"),
                html.Div(id="rates-describe-table"),
            ]
        ),
        class_name="mb-3",
    )
    return dbc.Container(
        [
            html.H2("Key rates", className="my-2"),
            control_bar,
            macro_chart_card("rates"),
            stats_card,
            macro_description_card("Key rates widget", rates_description_text),
        ],
        class_name="mt-2",
        fluid="md",
    )


@callback(
    Output("rates-chart", "figure"),
    Output("rates-chart", "config"),
    Output("rates-describe-table", "children"),
    Input("store", "data"),
    # Reactive page: every control is an Input — changing any of them
    # recalculates immediately, and the missing prevent_initial_call renders
    # the chart on page load. There is no Submit button.
    Input("rates-series", "value"),
    Input("rates-first-date", "value"),
    Input("rates-last-date", "value"),
)
def update_rates_page(screen, symbols, fd_value, ld_value):
    if not symbols or not dates_ready(fd_value, ld_value):
        raise dash.exceptions.PreventUpdate
    fd_value, ld_value = fd_value or None, ld_value or None
    try:
        objects = [macro_objects.get_rate_object(s, fd_value, ld_value) for s in symbols]
        fig = get_rates_figure(objects)
        stats_df = build_describe_table([obj.describe() for obj in objects])
        grid = build_stats_grid(stats_df, "rates-describe-table-grid", value_format="percent")
        fig, config = adopt_small_screens(fig, screen)
        return fig, config, grid
    except Exception as e:
        alert_fig = go.Figure()
        alert_fig.add_annotation(text=str(e), showarrow=False, font={"color": "red", "size": 14})
        return alert_fig, {}, None


@callback(
    Output("rates-series", "data"),
    Output("rates-series", "value"),
    Input("rates-group", "value"),
    # The layout already renders the right options/values for the URL-prefilled
    # group; firing on load would stomp prefilled tickers.
    prevent_initial_call=True,
)
def switch_rates_group(group: str):
    """Swap the series multiselect to the chosen group's catalog and defaults.

    The value change then triggers the reactive main callback; the group is
    deliberately NOT a main-callback Input (stale-series double-fire).
    """
    catalog = rates_group_catalog(group)
    defaults = RATES_GROUPS.get(group, RATES_GROUPS["key"])[2]
    options = [{"label": label, "value": symbol} for symbol, label in catalog.items()]
    return options, defaults


@callback(
    Output("rates-copy-link-button", "disabled"),
    Input("rates-series", "value"),
)
def disable_copy_link_rates(selected):
    # Empty selection disables Copy link (see inflation page).
    return make_submit_guard()(selected)


@callback(
    Output("rates-show-url", "children"),
    Input("rates-copy-link-button", "n_clicks"),
    State("rates-url", "href"),
    State("rates-series", "value"),
    State("rates-group", "value"),
    State("rates-first-date", "value"),
    State("rates-last-date", "value"),
)
def update_rates_link(n_clicks, href, symbols, group, first_date, last_date):
    return build_macro_link(
        href=href,
        tickers_list=symbols or [],
        first_date=first_date,
        last_date=last_date,
        group=(group, "key"),
    )


@callback(
    Output("rates-statistics-download", "data"),
    Input("rates-statistics-export-btn", "n_clicks"),
    State("rates-describe-table-grid", "rowData"),
    prevent_initial_call=True,
)
def export_rates_stats(n_clicks, row_data):
    return rowdata_to_xlsx_download(
        n_clicks, row_data, "rates_statistics.xlsx", column_formats=percent_column_formats(row_data)
    )


register_date_validation("rates-first-date")
register_date_validation("rates-last-date")

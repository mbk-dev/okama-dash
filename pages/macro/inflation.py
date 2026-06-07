"""/macro/inflation — inflation indexes with key-rate overlay (Macro section, stage 1)."""

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
from common.html_elements.submit_spinner import submit_spinner_running
from common.mobile_screens import adopt_small_screens
from common.parse_query import make_list_from_string
from pages.macro import macro_objects
from pages.macro.cards_macro.eng.inflation_description_txt import inflation_description_text
from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_controls import (
    date_columns,
    make_submit_guard,
    series_multiselect_column,
    submit_button_column,
)
from pages.macro.cards_macro.macro_description import macro_description_card
from pages.macro.cards_macro.macro_stats import build_describe_table, build_stats_grid
from pages.macro.macro_data import (
    INFLATION_DEFAULTS,
    INFLATION_SERIES,
    INFLATION_TO_KEY_RATE,
    KEY_RATES_SERIES,
    MACRO_FIRST_DATE_DEFAULT,
    filter_known,
)
from pages.macro.macro_link import build_macro_link

_Y_TITLES = {
    "annual": "Annual inflation, %",
    "rolling12m": "Rolling 12m inflation, %",
    "cumulative": "Cumulative inflation, %",
    "monthly": "Monthly inflation, %",
}
_SERIES_ATTRS = {
    "rolling12m": "rolling_inflation",
    "cumulative": "cumulative_inflation",
    "monthly": "values_monthly",
}
_OVERLAY_PLOTS = ("annual", "rolling12m")


def get_inflation_figure(objects: list, plot_type: str) -> go.Figure:
    labels = {obj.symbol: INFLATION_SERIES.get(obj.symbol, obj.symbol) for obj in objects}
    if plot_type == "annual":
        df = pd.concat([obj.annual_inflation_ts for obj in objects], axis=1) * 100
        df.columns = [labels[col] for col in df.columns]
        ind = df.index.to_timestamp(freq="Y")
        fig = px.bar(df, x=ind, y=df.columns, barmode="group", title="Annual inflation", height=600)
        fig.update_xaxes(dtick="M12", tickformat="%Y", ticklabelmode="instant")
    else:
        attr = _SERIES_ATTRS[plot_type]
        df = pd.concat([getattr(obj, attr) for obj in objects], axis=1) * 100
        df.columns = [labels[col] for col in df.columns]
        ind = df.index.to_timestamp("M")
        fig = px.line(df, x=ind, y=df.columns, title=_Y_TITLES[plot_type].rsplit(",", 1)[0], height=600)
        fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text=_Y_TITLES[plot_type], zeroline=True, zerolinecolor="black", zerolinewidth=1)
    fig.update_layout(xaxis_title=None, legend_title="Country")
    return fig


def add_key_rate_overlay(fig: go.Figure, symbols: list[str], first_date: str | None, last_date: str | None) -> None:
    """Overlay matching central-bank key rates as stepped dotted lines (same % axis)."""
    for symbol in symbols:
        rate_symbol = INFLATION_TO_KEY_RATE.get(symbol)
        if rate_symbol is None:
            continue
        rate_obj = macro_objects.get_rate_object(rate_symbol, first_date, last_date)
        values = rate_obj.values_monthly * 100
        fig.add_trace(
            go.Scatter(
                x=values.index.to_timestamp("M"),
                y=values.to_numpy(),
                mode="lines",
                line={"shape": "hv", "dash": "dot"},
                name=KEY_RATES_SERIES.get(rate_symbol, rate_symbol),
            )
        )


def get_purchasing_power_cards(objects: list) -> dbc.Row:
    """Accent cards: what 1000 units of each currency are worth after inflation."""
    cards = []
    for obj in objects:
        currency = obj.symbol.split(".", 1)[0]
        start = obj.first_date.strftime("%b %Y")
        end = obj.last_date.strftime("%b %Y")
        value = obj.purchasing_power_1000
        # Two decimals below 10 (e.g. 1.23 must not collapse to "1.2"); space
        # thousands separator with one decimal for larger values.
        value_txt = f"{value:,.1f}".replace(",", " ") if value >= 10 else f"{value:.2f}"
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(f"1000 {currency} ({start})", className="card-subtitle text-muted"),
                            html.H4(f"≈ {value_txt} {currency}", className="card-title mt-2"),
                            html.Small(f"purchasing power in {end}", className="text-muted"),
                        ]
                    )
                ),
                lg=4,
                md=6,
                sm=12,
                class_name="mb-2",
            )
        )
    return dbc.Row(cards, class_name="g-2 mb-2")


dash.register_page(
    __name__,
    path="/macro/inflation",
    title="Inflation : okama",
    name="Inflation",
    description=(
        "Okama.io widget: inflation indexes for Russia, USA, EU, UK, Israel and China — "
        "annual, rolling 12-month and cumulative inflation with central-bank key rates overlay"
    ),
)

_PLOT_OPTIONS = [
    {"label": "Annual inflation", "value": "annual"},
    {"label": "Rolling 12m", "value": "rolling12m"},
    {"label": "Cumulative", "value": "cumulative"},
    {"label": "Monthly", "value": "monthly"},
]
_PLOT_VALUES = {opt["value"] for opt in _PLOT_OPTIONS}

today_str = pd.Timestamp.today().strftime("%Y-%m")


def layout(tickers=None, first_date=None, last_date=None, plot=None, rates=None, **kwargs):
    selected = filter_known(make_list_from_string(tickers), INFLATION_SERIES) or INFLATION_DEFAULTS
    plot_type = plot if plot in _PLOT_VALUES else "annual"
    overlay_value = ["on"] if rates == "true" else []
    control_bar = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        series_multiselect_column("infl", INFLATION_SERIES, selected),
                        dbc.Col(
                            [
                                html.Label("Plot"),
                                dcc.Dropdown(
                                    options=_PLOT_OPTIONS,
                                    value=plot_type,
                                    clearable=False,
                                    id="infl-plot-type",
                                ),
                            ],
                            lg=2,
                            md=3,
                            sm=6,
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                options=[{"label": "Show key rates", "value": "on"}],
                                value=overlay_value,
                                id="infl-rates-overlay",
                                switch=True,
                            ),
                            width="auto",
                            class_name="align-self-end pb-2",
                        ),
                        *date_columns("infl", first_date or MACRO_FIRST_DATE_DEFAULT, last_date or today_str),
                        submit_button_column("infl"),
                    ],
                    class_name="g-2",
                    align="end",
                ),
                dbc.Row(
                    create_copy_link_div(
                        location_id="infl-url",
                        hidden_div_with_url_id="infl-show-url",
                        button_id="infl-copy-link-button",
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
                create_grid_header_with_export("Statistics", "infl-statistics-export-btn"),
                dcc.Download(id="infl-statistics-download"),
                html.Div(id="infl-describe-table"),
            ]
        ),
        class_name="mb-3",
    )
    return dbc.Container(
        [
            html.H2("Inflation", className="my-2"),
            control_bar,
            macro_chart_card("infl"),
            html.Div(id="infl-pp-cards"),
            stats_card,
            macro_description_card("Inflation widget", inflation_description_text),
        ],
        class_name="mt-2",
        fluid="md",
    )


@callback(
    Output("infl-chart", "figure"),
    Output("infl-chart", "config"),
    Output("infl-pp-cards", "children"),
    Output("infl-describe-table", "children"),
    Input("store", "data"),
    Input("infl-submit-button", "n_clicks"),
    State("infl-series", "value"),
    State("infl-plot-type", "value"),
    State("infl-rates-overlay", "value"),
    State("infl-first-date", "value"),
    State("infl-last-date", "value"),
    running=submit_spinner_running("infl-submit-spinner"),
    # NB: no prevent_initial_call — the chart auto-renders on page load (spec §4).
)
def update_inflation_page(screen, n_clicks, symbols, plot_type, overlay, fd_value, ld_value):
    if not symbols:
        raise dash.exceptions.PreventUpdate
    try:
        objects = [macro_objects.get_inflation_object(s, fd_value, ld_value) for s in symbols]
        fig = get_inflation_figure(objects, plot_type)
        if overlay and plot_type in _OVERLAY_PLOTS:
            add_key_rate_overlay(fig, symbols, fd_value, ld_value)
        pp_cards = get_purchasing_power_cards(objects)
        stats_df = build_describe_table([obj.describe() for obj in objects])
        stats_df = stats_df[stats_df["property"] != "1000 purchasing power"]
        grid = build_stats_grid(stats_df, "infl-describe-table-grid", value_format="percent")
        fig, config = adopt_small_screens(fig, screen)
        return fig, config, pp_cards, grid
    except Exception as e:
        alert_fig = go.Figure()
        alert_fig.add_annotation(text=str(e), showarrow=False, font={"color": "red", "size": 14})
        return alert_fig, {}, [], None


@callback(
    Output("infl-rates-overlay", "options"),
    Input("infl-plot-type", "value"),
)
def toggle_overlay_availability(plot_type: str) -> list[dict]:
    disabled = plot_type not in _OVERLAY_PLOTS
    return [{"label": "Show key rates", "value": "on", "disabled": disabled}]


@callback(
    Output("infl-submit-button", "disabled"),
    Output("infl-copy-link-button", "disabled"),
    Input("infl-series", "value"),
)
def disable_actions_inflation(selected):
    # Empty selection disables both actions: Submit (nothing to plot) and
    # Copy link (a "?tickers=" URL is broken). Unlike benchmark's
    # check_if_list_empty_or_big, no upper bound: CAPE10 legitimately
    # allows all 26 catalog countries.
    disabled = make_submit_guard()(selected)
    return disabled, disabled


@callback(
    Output("infl-show-url", "children"),
    Input("infl-copy-link-button", "n_clicks"),
    State("infl-url", "href"),
    State("infl-series", "value"),
    State("infl-plot-type", "value"),
    State("infl-rates-overlay", "value"),
    State("infl-first-date", "value"),
    State("infl-last-date", "value"),
)
def update_inflation_link(n_clicks, href, symbols, plot_type, overlay, first_date, last_date):
    return build_macro_link(
        href=href,
        tickers_list=symbols or [],
        first_date=first_date,
        last_date=last_date,
        plot=(plot_type, "annual"),
        rates=("true" if overlay else None, None),
    )


@callback(
    Output("infl-statistics-download", "data"),
    Input("infl-statistics-export-btn", "n_clicks"),
    State("infl-describe-table-grid", "rowData"),
    prevent_initial_call=True,
)
def export_inflation_stats(n_clicks, row_data):
    return rowdata_to_xlsx_download(
        n_clicks, row_data, "inflation_statistics.xlsx", column_formats=percent_column_formats(row_data)
    )


register_date_validation("infl-first-date")
register_date_validation("infl-last-date")

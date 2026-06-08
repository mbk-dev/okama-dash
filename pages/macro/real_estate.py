"""/macro/real-estate — Russian residential property prices (Macro section, stage 2).

RE symbols are assets (ok.Asset / ok.AssetList), not okama macro classes: prices
come per-Asset in native RUB; USD conversion goes through AssetList's private
_adjust_price_to_currency_monthly (no public converted-price API in okama 2.2 —
guarded by tests/unit/test_macro_objects.py); the wealth view plots
AssetList(inflation=True).wealth_indexes which already carries the ccy inflation
column.
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
from pages.macro.cards_macro.eng.real_estate_description_txt import real_estate_description_text
from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_download import register_macro_download
from pages.macro.cards_macro.macro_controls import (
    date_columns,
    dates_ready,
    make_submit_guard,
    series_multiselect_column,
)
from pages.macro.cards_macro.macro_description import macro_description_card
from pages.macro.cards_macro.macro_stats import build_stats_grid
from pages.macro.macro_data import MACRO_FIRST_DATE_DEFAULT, RE_DEFAULTS, RE_SERIES, filter_known
from pages.macro.macro_link import build_macro_link

_PRICE_Y_TITLES = {"RUB": "Price per m², RUB", "USD": "Price per m², USD"}


def trim_future(series: pd.Series) -> pd.Series:
    """Drop data points after the current month.

    Cheap insurance: the RE source once served dates ~9 months into the future
    (2026-06-07 incident, fixed upstream the same day) — forecast points must
    never render as facts.
    """
    now = pd.Timestamp.today().to_period("M")
    return series.loc[series.index <= now]


def get_re_price_figure(prices: dict[str, pd.Series], ccy: str) -> go.Figure:
    df = pd.concat(list(prices.values()), axis=1)
    df.columns = [RE_SERIES.get(symbol, symbol) for symbol in prices]
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="Real estate prices", height=600)
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text=_PRICE_Y_TITLES.get(ccy, f"Price per m², {ccy}"), zeroline=False)
    fig.update_layout(xaxis_title=None, legend_title="Market")
    return fig


def get_re_wealth_figure(al_object) -> go.Figure:
    df = al_object.wealth_indexes
    # Asset columns get market labels; the trailing inflation column keeps its
    # symbol name (RUB.INFL/USD.INFL) so the reference line is unambiguous.
    df = df.rename(columns={symbol: RE_SERIES[symbol] for symbol in RE_SERIES if symbol in df.columns})
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="Real estate wealth index vs inflation", height=600)
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text="Growth of 1000", zeroline=False)
    fig.update_layout(xaxis_title=None, legend_title="Market")
    return fig


dash.register_page(
    __name__,
    path="/macro/real-estate",
    title="Real estate RU : okama",
    name="Real Estate",
    description=(
        "Okama.io widget: Russian residential real estate prices — Moscow and Russia, "
        "primary and secondary markets, per-m² prices in RUB/USD and wealth index vs inflation"
    ),
)

_PLOT_OPTIONS = [
    {"label": "Price per m²", "value": "price"},
    {"label": "Wealth index", "value": "wealth"},
]
_PLOT_VALUES = {opt["value"] for opt in _PLOT_OPTIONS}
_CCY_OPTIONS = ["RUB", "USD"]

today_str = pd.Timestamp.today().strftime("%Y-%m")


def layout(tickers=None, first_date=None, last_date=None, plot=None, ccy=None, **kwargs):
    selected = filter_known(make_list_from_string(tickers), RE_SERIES) or RE_DEFAULTS
    plot_type = plot if plot in _PLOT_VALUES else "price"
    ccy_value = ccy.upper() if ccy and ccy.upper() in _CCY_OPTIONS else "RUB"
    control_bar = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        series_multiselect_column("re", RE_SERIES, selected),
                        dbc.Col(
                            [
                                html.Label("Plot"),
                                dcc.Dropdown(
                                    options=_PLOT_OPTIONS, value=plot_type, clearable=False, id="re-plot-type"
                                ),
                            ],
                            lg=2,
                            md=3,
                            sm=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Currency"),
                                dcc.Dropdown(options=_CCY_OPTIONS, value=ccy_value, clearable=False, id="re-ccy"),
                            ],
                            lg=1,
                            md=2,
                            sm=4,
                        ),
                        *date_columns("re", first_date or MACRO_FIRST_DATE_DEFAULT, last_date or today_str),
                    ],
                    class_name="g-2",
                    # Top-aligned: every column starts with a one-line Label, so
                    # the 38px controls land on one horizontal line.
                    align="start",
                ),
                dbc.Row(
                    create_copy_link_div(
                        location_id="re-url",
                        hidden_div_with_url_id="re-show-url",
                        button_id="re-copy-link-button",
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
                create_grid_header_with_export("Statistics", "re-statistics-export-btn"),
                dcc.Download(id="re-statistics-download"),
                html.Div(id="re-describe-table"),
            ]
        ),
        class_name="mb-3",
    )
    return dbc.Container(
        [
            html.H2("Real Estate", className="my-2"),
            control_bar,
            macro_chart_card("re"),
            stats_card,
            macro_description_card("Real Estate widget", real_estate_description_text),
        ],
        class_name="mt-2",
        fluid="md",
    )


def _price_series(symbols: list[str], ccy: str, fd: str | None, ld: str | None) -> dict[str, pd.Series]:
    """Per-symbol per-m² prices, converted to USD when asked, masked to dates."""
    al_object = None
    if ccy != "RUB":
        # Conversion needs an AssetList of the target currency (private okama
        # API — see the upgrade guard in tests/unit/test_macro_objects.py).
        al_object = macro_objects.get_asset_list_object(symbols, ccy=ccy, first_date=fd, last_date=ld)
    prices: dict[str, pd.Series] = {}
    for symbol in symbols:
        series = trim_future(macro_objects.get_asset_object(symbol).close_monthly)
        if al_object is not None:
            series = al_object._adjust_price_to_currency_monthly(series, "RUB")
            series.name = symbol
        if fd:
            series = series.loc[series.index >= pd.Period(fd, freq="M")]
        if ld:
            series = series.loc[series.index <= pd.Period(ld, freq="M")]
        prices[symbol] = series
    return prices


@callback(
    Output("re-chart", "figure"),
    Output("re-chart", "config"),
    Output("re-store-chart-data", "data"),
    Output("re-describe-table", "children"),
    Input("store", "data"),
    # Reactive page: every control is an Input — changing any of them
    # recalculates immediately, and the missing prevent_initial_call renders
    # the chart on page load. There is no Submit button.
    Input("re-series", "value"),
    Input("re-plot-type", "value"),
    Input("re-ccy", "value"),
    Input("re-first-date", "value"),
    Input("re-last-date", "value"),
)
def update_re_page(screen, symbols, plot_type, ccy, fd_value, ld_value):
    if not symbols or not dates_ready(fd_value, ld_value):
        raise dash.exceptions.PreventUpdate
    fd_value, ld_value = fd_value or None, ld_value or None
    try:
        if plot_type == "wealth":
            al_object = macro_objects.get_asset_list_object(
                symbols, ccy=ccy, first_date=fd_value, last_date=ld_value, inflation=True
            )
            fig = get_re_wealth_figure(al_object)
            store_df = al_object.wealth_indexes
        else:
            prices = _price_series(symbols, ccy, fd_value, ld_value)
            fig = get_re_price_figure(prices, ccy)
            store_df = pd.DataFrame(prices)
        # Stats always come from the inflation=True AssetList: describe() then
        # reports CAGR next to the inflation column — the core question of the
        # page ("does real estate beat inflation") in both plot modes.
        stats_al = macro_objects.get_asset_list_object(
            symbols, ccy=ccy, first_date=fd_value, last_date=ld_value, inflation=True
        )
        stats_df = stats_al.describe()
        # Crop service rows by NAME (robust to row-count differences between
        # the real okama frame and the mock shape).
        stats_df = stats_df[~stats_df["property"].isin(["Inception date", "Last asset date", "Common last data date"])]
        grid = build_stats_grid(stats_df, "re-describe-table-grid", value_format="percent")
        store_json = store_df.to_json(orient="split", default_handler=str)
        fig, config = adopt_small_screens(fig, screen)
        return fig, config, store_json, grid
    except Exception as e:
        alert_fig = go.Figure()
        alert_fig.add_annotation(text=str(e), showarrow=False, font={"color": "red", "size": 14})
        return alert_fig, {}, None, None


@callback(
    Output("re-copy-link-button", "disabled"),
    Input("re-series", "value"),
)
def disable_copy_link_re(selected):
    # Empty selection disables Copy link (see inflation page).
    return make_submit_guard()(selected)


@callback(
    Output("re-show-url", "children"),
    Input("re-copy-link-button", "n_clicks"),
    State("re-url", "href"),
    State("re-series", "value"),
    State("re-plot-type", "value"),
    State("re-ccy", "value"),
    State("re-first-date", "value"),
    State("re-last-date", "value"),
)
def update_re_link(n_clicks, href, symbols, plot_type, ccy, first_date, last_date):
    return build_macro_link(
        href=href,
        tickers_list=symbols or [],
        first_date=first_date,
        last_date=last_date,
        plot=(plot_type, "price"),
        ccy=(ccy, "RUB"),
    )


@callback(
    Output("re-statistics-download", "data"),
    Input("re-statistics-export-btn", "n_clicks"),
    State("re-describe-table-grid", "rowData"),
    prevent_initial_call=True,
)
def export_re_stats(n_clicks, row_data):
    return rowdata_to_xlsx_download(
        n_clicks, row_data, "real_estate_statistics.xlsx", column_formats=percent_column_formats(row_data)
    )


register_macro_download("re")
register_date_validation("re-first-date")
register_date_validation("re-last-date")

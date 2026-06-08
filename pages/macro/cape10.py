"""/macro/cape10 — CAPE10 valuation ratios for 26 countries (Macro section, stage 1)."""

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State

from common.html_elements.copy_link_div import create_copy_link_div
from common.mobile_screens import adopt_small_screens
from common.object_cache import TTL_EFFICIENT_FRONTIER, get_or_create
from common.parse_query import make_list_from_string
from pages.macro import macro_objects
from pages.macro.cards_macro.eng.cape10_description_txt import cape10_description_text
from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_controls import make_submit_guard, series_multiselect_column
from pages.macro.cards_macro.macro_description import macro_description_card
from pages.macro.cards_macro.macro_download import register_macro_download
from pages.macro.macro_data import CAPE10_DEFAULTS, CAPE10_SERIES, filter_known
from pages.macro.macro_link import build_macro_link

dash.register_page(
    __name__,
    path="/macro/cape10",
    title="CAPE10 : okama",
    name="CAPE10",
    description=(
        "Okama.io widget: CAPE10 (Shiller P/E) valuation ratio for 26 countries — "
        "history and current cross-country snapshot"
    ),
)

_PLOT_OPTIONS = [
    {"label": "History", "value": "history"},
    {"label": "Current snapshot", "value": "snapshot"},
]
_PLOT_VALUES = {opt["value"] for opt in _PLOT_OPTIONS}

# Highlight color = plotly default blue; muted grey for unselected countries.
_HIGHLIGHT_COLOR = "#636efa"
_MUTED_COLOR = "#c8d0dd"

today_str = pd.Timestamp.today().strftime("%Y-%m")


def get_cape_history_figure(objects: list) -> tuple[go.Figure, pd.DataFrame]:
    df = pd.concat([obj.values_monthly for obj in objects], axis=1)
    df.columns = [CAPE10_SERIES.get(col, col) for col in df.columns]
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="CAPE10 history", height=600)
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text="CAPE10", zeroline=False)
    fig.update_layout(xaxis_title=None, legend_title="Country")
    return fig, df


def get_cape_snapshot() -> pd.Series:
    """Latest CAPE10 for every catalog country (monthly data — cached per month)."""
    month = pd.Timestamp.today().strftime("%Y-%m")

    def build() -> pd.Series:
        values = {
            country: float(macro_objects.get_indicator_object(symbol, None, None).values_monthly.iloc[-1])
            for symbol, country in CAPE10_SERIES.items()
        }
        return pd.Series(values).sort_values()

    snapshot, _ = get_or_create(
        obj_type="cape_snapshot",
        constructor_fn=build,
        cache_key_params={"symbols": sorted(CAPE10_SERIES), "month": month},
        ttl_seconds=TTL_EFFICIENT_FRONTIER,
    )
    return snapshot


def get_cape_snapshot_figure(snapshot: pd.Series, selected_symbols: list[str]) -> go.Figure:
    selected_countries = {CAPE10_SERIES[s] for s in selected_symbols if s in CAPE10_SERIES}
    colors = [_HIGHLIGHT_COLOR if country in selected_countries else _MUTED_COLOR for country in snapshot.index]
    fig = go.Figure(
        go.Bar(
            x=snapshot.to_numpy(),
            y=list(snapshot.index),
            orientation="h",
            marker_color=colors,
            text=[f"{value:.1f}" for value in snapshot.to_numpy()],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="CAPE10 today: all countries (selected highlighted)",
        height=800,
        xaxis_title="CAPE10",
        margin={"l": 110},
    )
    # Headroom past the longest bar so its outside text label never clips.
    fig.update_xaxes(range=[0, float(snapshot.max()) * 1.15])
    return fig


def layout(tickers=None, first_date=None, last_date=None, plot=None, **kwargs):
    selected = filter_known(make_list_from_string(tickers), CAPE10_SERIES) or CAPE10_DEFAULTS
    plot_type = plot if plot in _PLOT_VALUES else "history"
    control_bar = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        series_multiselect_column("cape", CAPE10_SERIES, selected),
                        dbc.Col(
                            [
                                html.Label("Plot"),
                                dcc.Dropdown(
                                    options=_PLOT_OPTIONS, value=plot_type, clearable=False, id="cape-plot-type"
                                ),
                            ],
                            lg=2,
                            md=3,
                            sm=6,
                        ),
                    ],
                    class_name="g-2",
                    align="start",
                ),
                dbc.Row(
                    create_copy_link_div(
                        location_id="cape-url",
                        hidden_div_with_url_id="cape-show-url",
                        button_id="cape-copy-link-button",
                        card_name="widget",
                    ),
                ),
            ]
        ),
        class_name="mb-3",
    )
    return dbc.Container(
        [
            html.H2("CAPE10", className="my-2"),
            control_bar,
            macro_chart_card("cape"),
            macro_description_card("CAPE10 widget", cape10_description_text),
        ],
        class_name="mt-2",
        fluid="md",
    )


@callback(
    Output("cape-chart", "figure"),
    Output("cape-chart", "config"),
    Output("cape-store-chart-data", "data"),
    Input("store", "data"),
    Input("cape-series", "value"),
    Input("cape-plot-type", "value"),
)
def update_cape_page(screen, symbols, plot_type):
    if not symbols:
        raise dash.exceptions.PreventUpdate
    try:
        objects = [macro_objects.get_indicator_object(s, None, None) for s in symbols]
        if plot_type == "snapshot":
            snapshot = get_cape_snapshot()
            fig = get_cape_snapshot_figure(snapshot, symbols)
            store_df = snapshot.to_frame("CAPE10")
        else:
            fig, store_df = get_cape_history_figure(objects)
        store_json = store_df.to_json(orient="split", default_handler=str)
        fig, config = adopt_small_screens(fig, screen)
        if plot_type == "snapshot":
            fig.update_yaxes(ticklabelposition="outside")
        return fig, config, store_json
    except Exception as e:
        alert_fig = go.Figure()
        alert_fig.add_annotation(text=str(e), showarrow=False, font={"color": "red", "size": 14})
        return alert_fig, {}, None


@callback(
    Output("cape-copy-link-button", "disabled"),
    Input("cape-series", "value"),
)
def disable_copy_link_cape(selected):
    # Empty selection disables Copy link (see inflation page).
    return make_submit_guard()(selected)


@callback(
    Output("cape-show-url", "children"),
    Input("cape-copy-link-button", "n_clicks"),
    State("cape-url", "href"),
    State("cape-series", "value"),
    State("cape-plot-type", "value"),
)
def update_cape_link(n_clicks, href, symbols, plot_type):
    return build_macro_link(
        href=href,
        tickers_list=symbols or [],
        first_date=None,
        last_date=None,
        plot=(plot_type, "history"),
    )


register_macro_download("cape")

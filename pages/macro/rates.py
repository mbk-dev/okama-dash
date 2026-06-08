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

from common.html_elements.copy_link_div import create_copy_link_div
from common.mobile_screens import adopt_small_screens
from common.object_cache import TTL_EFFICIENT_FRONTIER, get_or_create
from common.parse_query import make_list_from_string
from pages.macro import macro_objects
from pages.macro.cards_macro.eng.rates_description_txt import rates_description_text
from pages.macro.cards_macro.macro_chart import macro_chart_card
from pages.macro.cards_macro.macro_controls import make_submit_guard, series_multiselect_column
from pages.macro.cards_macro.macro_description import macro_description_card
from pages.macro.cards_macro.macro_download import register_macro_download
from pages.macro.macro_data import (
    ALL_RATES_SERIES,
    MACRO_FIRST_DATE_DEFAULT,
    RATE_TO_INFLATION,
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


_PLOT_OPTIONS = [
    {"label": "Rates", "value": "history"},
    {"label": "Real rates", "value": "real"},
    {"label": "Current snapshot", "value": "snapshot"},
]
_PLOT_VALUES = {o["value"] for o in _PLOT_OPTIONS}
_HIGHLIGHT_COLOR = "#636efa"
_MUTED_COLOR = "#c8d0dd"


def _clip_to_default_start(df: pd.DataFrame) -> pd.DataFrame:
    """Clip to the 2000-01 default start.

    The page has no date controls, so without this the axis spans the full
    history: nominal rates reach back to 1954 (US_EFFR), and real rates inherit
    Russia's 1990s hyperinflation (real ЦБ rate to ~−2500%), which flattens
    every modern value. 2000-01 was the previous default start.
    """
    return df[df.index >= pd.Period(MACRO_FIRST_DATE_DEFAULT, freq="M")]


def get_rates_figure(objects: list) -> tuple[go.Figure, pd.DataFrame]:
    df = pd.concat([obj.values_monthly for obj in objects], axis=1) * 100
    df.columns = [ALL_RATES_SERIES.get(col, col) for col in df.columns]
    df = _clip_to_default_start(df)
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="Interest rates", height=600)
    fig.update_traces(line_shape="hv")  # rates change stepwise
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text="Rate, %", zeroline=True, zerolinecolor="black", zerolinewidth=1)
    fig.update_layout(xaxis_title=None, legend_title="Series")
    return fig, df


def get_real_rates_figure(pairs: dict) -> tuple[go.Figure, pd.DataFrame]:
    """pairs: {rate_symbol: (rate_obj, inflation_obj)} -> nominal − trailing-12m inflation."""
    if not pairs:
        # Unreachable in the normal flow (every grouped rate is in
        # RATE_TO_INFLATION), but a clear message beats an opaque empty-frame
        # RangeIndex.to_timestamp crash if an unmapped symbol ever slips through.
        raise ValueError("Real rates unavailable: the selected series have no inflation data")
    cols = {}
    for symbol, (rate_obj, infl_obj) in pairs.items():
        nominal = rate_obj.values_monthly
        infl = infl_obj.rolling_inflation
        common = nominal.index.intersection(infl.index)
        cols[ALL_RATES_SERIES.get(symbol, symbol)] = (nominal.loc[common] - infl.loc[common]) * 100
    df = _clip_to_default_start(pd.DataFrame(cols))
    ind = df.index.to_timestamp("M")
    fig = px.line(df, x=ind, y=df.columns, title="Real interest rates (nominal − 12m inflation)", height=600)
    fig.update_traces(line_shape="hv")
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text="Real rate, %", zeroline=True, zerolinecolor="black", zerolinewidth=1)
    fig.update_layout(xaxis_title=None, legend_title="Series")
    return fig, df


def _group_of(symbols: list[str]) -> str:
    for group, (_, catalog, _) in RATES_GROUPS.items():
        if any(s in catalog for s in symbols):
            return group
    return "key"


def get_rates_snapshot(group: str) -> pd.Series:
    """Latest rate (%) for every series in the group (cached per month)."""
    month = pd.Timestamp.today().strftime("%Y-%m")
    catalog = rates_group_catalog(group)

    def build() -> pd.Series:
        values = {
            ALL_RATES_SERIES.get(sym, sym): float(
                macro_objects.get_rate_object(sym, None, None).values_monthly.iloc[-1]
            )
            * 100
            for sym in catalog
        }
        return pd.Series(values).sort_values()

    snapshot, _ = get_or_create(
        obj_type="rates_snapshot",
        constructor_fn=build,
        cache_key_params={"symbols": sorted(catalog), "month": month},
        ttl_seconds=TTL_EFFICIENT_FRONTIER,
    )
    return snapshot


def get_rates_snapshot_figure(snapshot: pd.Series, selected_labels: set) -> go.Figure:
    colors = [_HIGHLIGHT_COLOR if name in selected_labels else _MUTED_COLOR for name in snapshot.index]
    fig = go.Figure(
        go.Bar(
            x=snapshot.to_numpy(),
            y=list(snapshot.index),
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}" for v in snapshot.to_numpy()],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Current rates (selected highlighted)", height=600, xaxis_title="Rate, %", margin={"l": 160}
    )
    fig.update_xaxes(range=[min(0.0, float(snapshot.min()) * 1.15), float(snapshot.max()) * 1.15])
    return fig


def layout(tickers=None, plot=None, group=None, **kwargs):
    group_value = group if group in RATES_GROUPS else "key"
    catalog = rates_group_catalog(group_value)
    group_defaults = RATES_GROUPS[group_value][2]
    selected = filter_known(make_list_from_string(tickers), catalog) or group_defaults
    plot_type = plot if plot in _PLOT_VALUES else "history"
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
                        dbc.Col(
                            [
                                html.Label("Plot"),
                                dcc.Dropdown(
                                    options=_PLOT_OPTIONS, value=plot_type, clearable=False, id="rates-plot-type"
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
    return dbc.Container(
        [
            html.H2("Key rates", className="my-2"),
            control_bar,
            macro_chart_card("rates"),
            macro_description_card("Key rates widget", rates_description_text),
        ],
        class_name="mt-2",
        fluid="md",
    )


@callback(
    Output("rates-chart", "figure"),
    Output("rates-chart", "config"),
    Output("rates-store-chart-data", "data"),
    Input("store", "data"),
    Input("rates-series", "value"),
    Input("rates-plot-type", "value"),
)
def update_rates_page(screen, symbols, plot_type):
    if not symbols:
        raise dash.exceptions.PreventUpdate
    try:
        if plot_type == "snapshot":
            group = _group_of(symbols)
            snapshot = get_rates_snapshot(group)
            selected = {ALL_RATES_SERIES.get(s, s) for s in symbols}
            fig = get_rates_snapshot_figure(snapshot, selected)
            store_df = snapshot.to_frame("Rate, %")
        elif plot_type == "real":
            pairs = {
                s: (
                    macro_objects.get_rate_object(s, None, None),
                    macro_objects.get_inflation_object(RATE_TO_INFLATION[s], None, None),
                )
                for s in symbols
                if s in RATE_TO_INFLATION
            }
            fig, store_df = get_real_rates_figure(pairs)
        else:
            objects = [macro_objects.get_rate_object(s, None, None) for s in symbols]
            fig, store_df = get_rates_figure(objects)
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
    State("rates-plot-type", "value"),
)
def update_rates_link(n_clicks, href, symbols, group, plot):
    return build_macro_link(
        href=href,
        tickers_list=symbols or [],
        first_date=None,
        last_date=None,
        group=(group, "key"),
        plot=(plot, "history"),
    )


register_macro_download("rates")

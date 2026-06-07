"""/macro/inflation — inflation indexes with key-rate overlay (Macro section, stage 1)."""

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html

from pages.macro import macro_objects
from pages.macro.macro_data import INFLATION_SERIES, INFLATION_TO_KEY_RATE, KEY_RATES_SERIES

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

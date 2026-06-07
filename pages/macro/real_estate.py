"""/macro/real-estate — Russian residential property prices (Macro section, stage 2).

RE symbols are assets (ok.Asset / ok.AssetList), not okama macro classes: prices
come per-Asset in native RUB; USD conversion goes through AssetList's private
_adjust_price_to_currency_monthly (no public converted-price API in okama 2.2 —
guarded by tests/unit/test_macro_objects.py); the wealth view plots
AssetList(inflation=True).wealth_indexes which already carries the ccy inflation
column.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pages.macro.macro_data import RE_SERIES

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

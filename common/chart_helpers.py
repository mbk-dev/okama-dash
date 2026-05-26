import logging

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import okama as ok

import common.settings as settings


def make_error_alert(error: Exception) -> dbc.Alert:
    logging.exception("Callback error")
    return dbc.Alert(f"Error: {error}", color="danger", dismissable=True)
import common.crisis.crisis_data as cr


def add_inflation_trace(fig: go.Figure, ind, df: pd.DataFrame) -> None:
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


def add_crisis_rectangles(fig: go.Figure, chart_first_date, chart_last_date) -> None:
    for crisis in cr.crisis_list:
        if chart_first_date < crisis.first_date_dt and chart_last_date > crisis.last_date_dt:
            fig.add_vrect(
                x0=crisis.first_date,
                x1=crisis.last_date,
                annotation_text=crisis.name,
                annotation=dict(align="left", valign="top", textangle=-90),
                fillcolor="red",
                opacity=0.25,
                line_width=0,
            )


def add_last_value_annotations(fig: go.Figure, annotations_xy, annotations_text) -> None:
    for (x, y), text in zip(annotations_xy, annotations_text):
        fig.add_annotation(
            x=x,
            y=y,
            text=text,
            showarrow=False,
            xanchor="left",
            bgcolor="grey",
        )


def get_rf_rate(al_object) -> float:
    inflation_ts = al_object.inflation_ts if hasattr(al_object, "inflation") else pd.Series()
    inflation = ok.Frame.get_cagr(inflation_ts) if not inflation_ts.empty else None
    return inflation if inflation else settings.RISK_FREE_RATE_DEFAULT


def add_sharpe_ratio_row(al_object, statistics_df: pd.DataFrame) -> pd.DataFrame:
    rf_rate = get_rf_rate(al_object)
    sh_ratio = al_object.get_sharpe_ratio(rf_return=rf_rate)
    if isinstance(sh_ratio, pd.Series):
        row = sh_ratio.to_dict()
    else:
        row = {al_object.symbol: sh_ratio}
    row.update(
        period=al_object._pl_txt,
        property=f"Sharpe ratio (risk free rate: {rf_rate * 100:.2f})",
    )
    return pd.concat([statistics_df, pd.DataFrame(row, index=[0])], ignore_index=True)

"""Chart card for macro pages: full-bleed on mobile, spinner while loading."""

import dash_bootstrap_components as dbc
from dash import dcc


def macro_chart_card(page_prefix: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(dcc.Loading(dcc.Graph(id=f"{page_prefix}-chart"))),
        class_name="chart-card mb-3",
    )

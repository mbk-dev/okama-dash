"""Bottom description card for macro pages (indicator explainer)."""

import dash_bootstrap_components as dbc
from dash import html


def macro_description_card(title: str, children) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([html.Div([html.H4(children=title), html.Div(children)])]),
        class_name="my-3",
    )

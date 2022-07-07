import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

import pandas as pd

from application import settings as settings, inflation as inflation
from application.symbols import get_symbols
from application import cache

app = dash.get_app()
cache.init_app(app.server)

today_str = pd.Timestamp.today().strftime("%Y-%m")
card_controls = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Efficient Frontier", className="card-title"),
            html.Div(
                [
                    html.Label("Tickers in the Efficient Frontier"),
                    dcc.Dropdown(
                        options=get_symbols(),
                        value=settings.default_symbols,
                        multi=True,
                        placeholder="Select assets",
                        id="ef-symbols-list",
                    ),
                ],
            ),
            html.Div(
                [
                    html.Label("Base currency"),
                    dcc.Dropdown(
                        options=inflation.get_currency_list(),
                        value="USD",
                        multi=False,
                        placeholder="Select a base currency",
                        id="ef-base-currency",
                    ),
                ],
            ),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("First Date"),
                                    dbc.Input(
                                        id="ef-first-date", value="2000-01", type="text"
                                    ),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            ),
                            dbc.Col(
                                [
                                    html.Label("Last Date"),
                                    dbc.Input(
                                        id="ef-last-date", value=today_str, type="text"
                                    ),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            ),
                        ]
                    )
                ]
            ),
            html.Div(
                [
                    dbc.Button(
                        children="Get the Efficient Frontier",
                        id="ef-submit-button-state",
                        n_clicks=0,
                        color="primary",
                    ),
                ],
                style={"text-align": "center"},
                className="p-3",
            ),
        ]
    ),
    class_name="mb-3",
)

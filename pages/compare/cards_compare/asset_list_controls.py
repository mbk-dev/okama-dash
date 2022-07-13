import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

import pandas as pd

from common import settings as settings, inflation as inflation
from common.symbols import get_symbols
from common import cache

app = dash.get_app()
cache.init_app(app.server)

today_str = pd.Timestamp.today().strftime("%Y-%m")
card_controls = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Compare Assets", className="card-title"),
            html.Div(
                [
                    html.Label("Tickers to compare"),
                    dcc.Dropdown(
                        options=get_symbols(),
                        value=settings.default_symbols,
                        multi=True,
                        placeholder="Select assets",
                        id="symbols-list",
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
                        id="base-currency",
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
                                        id="first-date", value="2000-01", type="text"
                                    ),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            ),
                            dbc.Col(
                                [
                                    html.Label("Last Date"),
                                    dbc.Input(
                                        id="last-date", value=today_str, type="text"
                                    ),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            ),
                        ]
                    ),
                    dbc.Row(html.H5(children="Options")),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(["Include Inflation",
                                               html.I(className="bi bi-info-square ms-2", id="al-info-inflation")]),
                                    dbc.Checklist(
                                        options=[
                                            {"label": "", "value": "inflation-on"},
                                        ],
                                        value=[],
                                        id="al-inflation-option",
                                        inline=True,
                                        switch=True,
                                    ),
                                    dbc.Tooltip(
                                        "If enabled, inflation will be displayed on the chart. However, with inflation "
                                        "turned on, the chart statistics will not include last month data, as "
                                        "inflation statistics are delayed.",
                                        target="al-info-inflation",
                                        # className="text-start"
                                    )
                                ],
                                lg=12, md=12, sm=12,
                                # class_name="pt-4 pt-sm-4 pt-md-1"
                            ),
                        ]
                    )
                ]
            ),
            html.Div(
                [
                    dbc.Button(
                        children="Compare",
                        id="submit-button-state",
                        n_clicks=0,
                        color="primary",
                    ),
                ],
                style={"text-align":"center"},
                className="p-3",
            ),
        ]
    ),
    class_name="mb-3",
)

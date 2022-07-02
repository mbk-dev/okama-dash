import dash_bootstrap_components as dbc
from dash import html, dcc

import pandas as pd

import inflation
import settings
import symbols

today_str = pd.Timestamp.today().strftime('%Y-%m')

card_controls = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Settings", className="card-title"),
            html.Div([
                html.Label("Tickers to compare"),
                dcc.Dropdown(
                    options=symbols.get_symbols(),
                    value=settings.default_symbols,
                    multi=True,
                    placeholder="Select assets",
                    id='symbols-list'
                )],
                # style={'width': '48%', 'display': 'inline-block'}
            ),
            # html.Br(),
            html.Div(
                [
                    html.Label("Base currency"),
                    dcc.Dropdown(
                        options=inflation.get_currency_list(),
                        value='USD',
                        multi=False,
                        placeholder="Select a base currency",
                        id='base-currency'
                    )
                ],
                # style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
                ),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("First Date"),
                                    dbc.Input(id='first-date', value='2000-01', type='text'),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            ),
                            dbc.Col(
                                [
                                    html.Label("Last Date"),
                                    dbc.Input(id='last-date', value=today_str, type='text'),
                                    dbc.FormText("Format: YYYY-MM"),
                                ]
                            )
                        ]
                    )

                ]
            ),
            # html.P(
            #     html.Button(id='submit-button-state', n_clicks=0, children='Submit')
            # ),
            html.Div(
                [
                    dbc.Button(children="Compare", id='submit-button-state', n_clicks=0, color="primary"),
                ],
                className="d-grid gap-2 col-1 mx-auto",
            )

        ]
    ),
    class_name="mb-3",
)

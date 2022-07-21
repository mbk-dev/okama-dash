from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import html, dcc, callback

import pandas as pd

from common import settings as settings, inflation as inflation
from common.parse_query import get_tickers_list
from common.symbols import get_symbols
from common import cache

app = dash.get_app()
cache.init_app(app.server)

today_str = pd.Timestamp.today().strftime("%Y-%m")


def card_controls(tickers: Optional[list],
                  first_date: Optional[str],
                  last_date: Optional[str],
                  ccy: Optional[str]
                  ):
    tickers_list = get_tickers_list(tickers)
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Compare Assets", className="card-title"),
                html.Div(
                    [
                        html.Label("Tickers to compare"),
                        dcc.Dropdown(
                            options=get_symbols(),
                            value=tickers_list if tickers_list else settings.default_symbols,
                            multi=True,
                            placeholder="Select assets",
                            id="symbols-list",
                        ),
                    ],
                ),
                # html.Div(
                #     children=tickers,
                #     id="hidden-div",
                #     hidden=True,
                # ),
                html.Div(
                    [
                        html.Label("Base currency"),
                        dcc.Dropdown(
                            options=inflation.get_currency_list(),
                            value=ccy if ccy else "USD",
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
                                            id="first-date",
                                            value=first_date if first_date else "2000-01",
                                            type="text"
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Last Date"),
                                        dbc.Input(
                                            id="last-date",
                                            value=last_date if last_date else today_str,
                                            type="text"
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                html.Div(
                                    [
                                        # represents the URL bar, doesn't render anything
                                        dcc.Location(id='url', refresh=False),
                                        # content will be rendered in this element
                                        # html.Div(id='show_url'),
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    [
                                                        "Copy link",
                                                        html.I(className="bi bi-share ms-2"),
                                                        dcc.Clipboard(
                                                            target_id="show_url",
                                                            className="position-absolute start-0 top-0 h-100 w-100 opacity-0",
                                                        ),
                                                    ],
                                                    id="al-copy-link-button",
                                                    className="position-relative",
                                                    color="link",
                                                    outline=False
                                                ),
                                                html.Div(
                                                    children="",
                                                    hidden=True,
                                                    id="show_url"
                                                ),
                                                dbc.Tooltip(
                                                    "Сopy asset list link to clipboard",
                                                    target="al-copy-link-button",
                                                )

                                            ],
                                            style={"text-align": "center"},
                                        )
                                    ]
                                )
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
    return card


@callback(
    Output('show_url', 'children'),
    Input('url', 'href'),
    Input('symbols-list', 'value'),
    Input('base-currency', 'value'),
    Input('first-date', 'value'),
    Input('last-date', 'value')
          )
def update_content(href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str):
    tickers_str = ""
    t_number = len(tickers_list)
    for i, ticker in enumerate(tickers_list):
        tickers_str += f"{ticker}," if i + 1 < t_number else ticker
    reset_href = href.split("?")[0]
    new_url = f"{reset_href}?tickers={tickers_str}" if tickers_str else reset_href
    new_url += f"&ccy={ccy}"
    new_url += f"&first_date={first_date}"
    new_url += f"&last_date={last_date}"
    return new_url

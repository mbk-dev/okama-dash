import re
from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import html, dcc, callback

import pandas as pd

from common import settings as settings, inflation as inflation
from common.create_link import create_link
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import get_tickers_list
from common.symbols import get_symbols
from common import cache

app = dash.get_app()
cache.init_app(app.server)
options = get_symbols()

today_str = pd.Timestamp.today().strftime("%Y-%m")


def card_controls(
    tickers: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
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
                            options=options,
                            value=tickers_list
                            if tickers_list
                            else settings.default_symbols,
                            multi=True,
                            placeholder="Select assets",
                            id="al-symbols-list",
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Label("Base currency"),
                        dcc.Dropdown(
                            options=inflation.get_currency_list(),
                            value=ccy if ccy else "USD",
                            multi=False,
                            placeholder="Select a base currency",
                            id="al-base-currency",
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
                                            id="al-first-date",
                                            value=first_date
                                            if first_date
                                            else "2000-01",
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Last Date"),
                                        dbc.Input(
                                            id="al-last-date",
                                            value=last_date if last_date else today_str,
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                            ]
                        ),
                        dbc.Row(
                            # copy link to clipboard button
                            create_copy_link_div(
                                location_id="al-url",
                                hidden_div_with_url_id="al-show-url",
                                button_id="al-copy-link-button",
                                card_name="asset list",
                            ),
                        ),
                        dbc.Row(html.H5(children="Options")),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Include Inflation",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="al-info-inflation",
                                                ),
                                            ]
                                        ),
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
                                        ),
                                    ],
                                    lg=12,
                                    md=12,
                                    sm=12,
                                    # class_name="pt-4 pt-sm-4 pt-md-1"
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    [
                        dbc.Button(
                            children="Compare",
                            id="al-submit-button",
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
    return card


@callback(
    Output("al-show-url", "children"),
    Input("al-url", "href"),
    Input("al-symbols-list", "value"),  # get selected tickers
    Input("al-base-currency", "value"),
    Input("al-first-date", "value"),
    Input("al-last-date", "value"),
)
def update_link_al(
    href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str
):
    return create_link(ccy, first_date, href, last_date, tickers_list)


@app.callback(
    Output("al-symbols-list", "options"),
    Input("al-symbols-list", "search_value"),
    Input("al-symbols-list", "value"),
)
def optimize_search_al(search_value, selected_values):
    return [o for o in options if re.match(search_value, o, re.IGNORECASE) or o in (selected_values or [])] \
        if search_value else selected_values

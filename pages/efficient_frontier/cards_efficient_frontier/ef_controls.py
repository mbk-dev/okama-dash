import re
from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output

import pandas as pd

from common import settings as settings, inflation as inflation
from common.create_link import create_link
from common.html_elements.copy_link_div import create_copy_link_div
from common.symbols import get_symbols
from common import cache
import pages.efficient_frontier.cards_efficient_frontier.eng.ef_tooltips_options_txt as tl

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
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Efficient Frontier", className="card-title"),
                html.Div(
                    [
                        html.Label("Tickers in the Efficient Frontier"),
                        dcc.Dropdown(
                            options=options,
                            value=tickers if tickers else settings.default_symbols,
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
                            value=ccy if ccy else "USD",
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
                                            id="ef-first-date",
                                            value=first_date if first_date else "2000-01",
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Last Date"),
                                        dbc.Input(
                                            id="ef-last-date",
                                            value=last_date if last_date else today_str,
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ],
                                ),
                            ]
                        ),
                        dbc.Row(
                            # copy link to clipboard button
                            create_copy_link_div(
                                location_id="ef-url",
                                hidden_div_with_url_id="ef-show-url",
                                button_id="ef-copy-link-button",
                                card_name="Efficient Frontier",
                            )
                        ),
                        dbc.Row(html.H5(children="Options")),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Rate of Return",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-ror",
                                                ),
                                            ]
                                        ),
                                        # data-toggle="tooltip",
                                        # data-original-title="Optionally render"),
                                        dbc.RadioItems(
                                            options=[
                                                {
                                                    "label": "Geometric mean",
                                                    "value": "Geometric",
                                                },
                                                {
                                                    "label": "Arithemtic mean",
                                                    "value": "Arithmetic",
                                                },
                                            ],
                                            value="Geometric",
                                            id="rate-of-return-options",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_ror,
                                            target="info-ror",
                                            # className="text-start"
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Capital Market Line (CML)",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-cml",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "On", "value": "On"},
                                                {"label": "Off", "value": "Off"},
                                            ],
                                            value="Off",
                                            id="cml-option",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_cml,
                                            target="info-cml",
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Risk-Free Rate",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-rf-rate",
                                                ),
                                            ]
                                        ),
                                        dbc.Input(
                                            type="number",
                                            min=0,
                                            max=100,
                                            value=0,
                                            id="risk-free-rate-option",
                                        ),
                                        dbc.FormText("0 - 100 (Format: XX.XX)"),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_rf_rate,
                                            target="info-rf-rate",
                                        ),
                                    ],
                                    lg=4,
                                    md=4,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                            ]
                        ),
                        dbc.Row(html.H5(children="Monte-Carlo Simulation")),
                        dbc.Row(
                            [
                                # html.Hr(),
                                dbc.Label(
                                    [
                                        "Number of points",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="info-monte-carlo",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            type="number",
                                            min=0,
                                            max=100000,
                                            value=0,
                                            id="monte-carlo-option",
                                        ),
                                        dbc.FormFeedback("", type="valid"),
                                        dbc.FormFeedback(
                                            f"it should be an integer number ≤{settings.MC_MAX}", type="invalid"
                                        ),
                                        # dbc.FormText("≤100 000")
                                    ],
                                    width=6
                                ),
                                dbc.Tooltip(
                                    tl.ef_options_monte_carlo,
                                    target="info-monte-carlo",
                                ),
                            ],
                            className="p-1",
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
    return card


@callback(
    Output(component_id="risk-free-rate-option", component_property="disabled"),
    Input(component_id="cml-option", component_property="value"),
)
def update_risk_free_rate(cml: str):
    return cml == "Off"


@callback(
    Output("ef-show-url", "children"),
    Input("ef-url", "href"),
    Input("ef-symbols-list", "value"),
    Input("ef-base-currency", "value"),
    Input("ef-first-date", "value"),
    Input("ef-last-date", "value"),
)
def update_link_ef(href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str):
    return create_link(ccy, first_date, href, last_date, tickers_list)


@app.callback(
    Output("ef-symbols-list", "options"),
    Input("ef-symbols-list", "search_value"),
    Input("ef-symbols-list", "value"),
)
def optimize_search_ef(search_value, selected_values):
    return (
        [o for o in options if re.match(search_value, o, re.IGNORECASE) or o in (selected_values or [])]
        if search_value
        else selected_values
    )


@app.callback(
    Output("monte-carlo-option", "valid"),
    Output("monte-carlo-option", "invalid"),
    Input("monte-carlo-option", "value"),
)
def check_validity_monte_carlo(number: int):
    """
    Check if input is an integer in range for 0 to MC_MAX.
    """
    if number:
        is_correct_number = number in range(0, settings.MC_MAX) and isinstance(number, int)
        return is_correct_number, not is_correct_number
    return False, False

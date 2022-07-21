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
                                            value=first_date
                                            if first_date
                                            else "2000-01",
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
                                            "Geometric mean or Compound annual growth rate (CAGR) is the rate of return "
                                            "that would be required for an investment to grow from its initial to its "
                                            "final value, assuming all incomes were reinvested. "
                                            "Arithmetic mean - annualized mean return (arithmetic mean) for "
                                            "the rate of return monthly time series.",
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
                                            "The Capital Market Line (CML) is the tangent line drawn from the point of "
                                            "the risk-free asset (volatility is zero) to the point of tangency portfolio "
                                            "or Maximum Sharpe Ratio (MSR) point."
                                            "The slope of the CML is the Sharpe ratio of the tangency portfolio.",
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
                                            "Risk-free Rate of Return is the theoretical rate of return of "
                                            "an investment with zero risk. Risk-free Rate required to calculate "
                                            "Sharpe Ratio, Tangency portfolio and plot Capital Market Line (CML).",
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
def update_link_ef(
    href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str
):
    return create_link(ccy, first_date, href, last_date, tickers_list)


#
# @app.callback(
#     Output("ef-symbols-list", "options"),
#     Input("ef-symbols-list", "search_value"),
#     State("ef-symbols-list", "value"),
# )
# def update_options(search_value, value):
#     if not search_value:
#         raise PreventUpdate
#     opt_list = [
#         o for o in options if re.match(search_value, o, re.IGNORECASE) or o in (value or [])
#     ]
#     return opt_list

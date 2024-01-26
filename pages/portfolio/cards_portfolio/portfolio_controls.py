"""
test URL:
http://127.0.0.1:8050/portfolio?tickers=SPY.US,BND.US,GLD.US&weights=30,20,50&first_date=2015-01&last_date=2020-12&ccy=RUB&rebal=year
"""

import re
from typing import Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback, ALL, MATCH

import pandas as pd
from dash.exceptions import PreventUpdate

from common import settings as settings, inflation as inflation
from common.create_link import create_link
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import make_list_from_string
from common.symbols import get_symbols
from common import cache
import common.validators as validators
from pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt import (
    pf_options_tooltip_inflation,
    pf_options_tooltip_cagr,
    pf_options_window,
    pf_rebalancing_period,
)

app = dash.get_app()
cache.init_app(app.server)
options = get_symbols()

today_str = pd.Timestamp.today().strftime("%Y-%m")


def card_controls(
    tickers: Optional[list],
    weights: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
    rebal: Optional[str],
):
    tickers_list = make_list_from_string(tickers, char_type="str")
    weights_list = make_list_from_string(weights, char_type="float")
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Investment Portfolio", className="card-title"),
                html.Div(
                    [
                        dbc.Row([dbc.Col(html.Label("Tickers")), dbc.Col(html.Label("Weights"))]),
                        html.Div(id="dynamic-container", children=[]),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Button("Add Asset", id="dynamic-add-filter", n_clicks=0)),
                                dbc.Col(html.Div(id="pf-portfolio-weights-sum")),
                            ]
                        ),
                    ],
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Base currency"),
                                dcc.Dropdown(
                                    options=inflation.get_currency_list(),
                                    value=ccy if ccy else "USD",
                                    multi=False,
                                    placeholder="Select a base currency",
                                    id="pf-base-currency",
                                ),
                            ],
                        ),
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Rebalancing period",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-info-rebalancing",
                                        ),
                                    ]
                                ),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Monthly", "value": "month"},
                                        {"label": "Quarter", "value": "quarter"},
                                        {"label": "Half-year", "value": "half-year"},
                                        {"label": "Every year", "value": "year"},
                                        {"label": "Not rebalanced", "value": "none"},
                                    ],
                                    value=rebal if rebal else "month",
                                    multi=False,
                                    placeholder="Select a rebalancing period",
                                    id="pf-rebalancing-period",
                                ),
                                dbc.Tooltip(
                                    pf_rebalancing_period,
                                    target="pf-info-rebalancing",
                                ),
                            ],
                        ),
                    ]
                ),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("First Date"),
                                        dbc.Input(
                                            id="pf-first-date",
                                            value=first_date if first_date else "2000-01",
                                            type="text",
                                        ),
                                        dbc.FormText("Format: YYYY-MM"),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Last Date"),
                                        dbc.Input(
                                            id="pf-last-date",
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
                                location_id="pf-url",
                                hidden_div_with_url_id="pf-show-url",
                                button_id="pf-copy-link-button",
                                card_name="Portfolio",
                            ),
                        ),
                        dbc.Row(html.H5(children="Options")),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Plot:",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-plot",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "Wealth Index", "value": "wealth"},
                                                {"label": "Rolling Cagr", "value": "cagr"},
                                                {"label": "Rolling Real Cagr", "value": "real_cagr"},
                                                {"label": "Drawdowns", "value": "drawdowns"},
                                            ],
                                            value="wealth",
                                            id="pf-plot-option",
                                        ),
                                        dbc.Tooltip(
                                            pf_options_tooltip_cagr,
                                            target="pf-info-plot",
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
                                                "Include Inflation",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-inflation",
                                                ),
                                            ]
                                        ),
                                        dbc.Switch(
                                            label="",
                                            value=False,
                                            id="pf-inflation-switch",
                                        ),
                                        dbc.Tooltip(
                                            pf_options_tooltip_inflation,
                                            target="pf-info-inflation",
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
                                                "Rolling Window",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-rolling",
                                                ),
                                            ]
                                        ),
                                        dbc.Input(
                                            type="number",
                                            min=1,
                                            value=2,
                                            id="pf-rolling-window",
                                        ),
                                        dbc.FormText("Format: number of years (≥ 1)"),
                                        dbc.Tooltip(
                                            pf_options_window,
                                            target="pf-info-rolling",
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
                            children="Submit",
                            id="pf-submit-button",
                            n_clicks=0,
                            color="primary",
                        ),
                    ],
                    style={"text-align": "center"},
                    className="p-3",
                ),
                dcc.Store(id="pf_tickers_url", data=tickers_list),
                dcc.Store(id="pf_weights_url", data=weights_list),
            ]
        ),
        class_name="mb-3",
    )
    return card


@callback(
    Output(component_id="pf-rolling-window", component_property="disabled"),
    Input(component_id="pf-plot-option", component_property="value"),
)
def update_rolling_input(plot_options: str) -> bool:
    return plot_options in {"wealth", "drawdowns"}


@callback(
    Output(component_id="pf-inflation-switch", component_property="value"),
    Output(component_id="pf-inflation-switch", component_property="disabled"),
    Input(component_id="pf-plot-option", component_property="value"),
    State(component_id="pf-inflation-switch", component_property="value"),
)
def update_inflation_switch(plot_options: str, inflation_switch_value) -> Tuple[bool, bool]:
    """
    Change inflation-switch value and disabled state.

    It should be "ON" and "Disabled" if "Real CAGR" chart selected.
    """
    if plot_options == "real_cagr":
        return True, True
    elif plot_options == "drawdowns":
        return False, True
    else:
        return inflation_switch_value, False

@app.callback(
    Output("pf-logarithmic-scale-switch-div", "hidden"),
    Input(component_id="pf-submit-button", component_property="n_clicks"),
    State(component_id="pf-plot-option", component_property="value"),
)
def show_log_scale_switch(n_clicks, plot_type: str):
    return plot_type not in ("wealth",)


@callback(
    Output("pf-show-url", "children"),
    Input("pf-copy-link-button", "n_clicks"),
    State("pf-url", "href"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    State("pf-base-currency", "value"),
    State("pf-first-date", "value"),
    State("pf-last-date", "value"),
    State("pf-rebalancing-period", "value"),
    prevent_initial_call=True,
)
def update_link_pf(
    n_clicks: int,
    href: str,
    tickers_list: Optional[list],
    weights_list: Optional[list],
    ccy: str,
    first_date: str,
    last_date: str,
    rebal: str,
):
    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        weights_list=weights_list,
        rebal=rebal,
    )


# ----------------------- Ticker | Weight constructor -------------------------------------------
@app.callback(
    Output("dynamic-container", "children"),
    Input("pf_tickers_url", "data"),
    Input("pf_weights_url", "data"),
    Input("dynamic-add-filter", "n_clicks"),
    State("dynamic-container", "children"),
)
def add_rows_to_constructor(tickers, weights, n_clicks, children):
    if n_clicks == 0 and tickers:
        for symbol, weight in zip(tickers, weights):
            children = append_row(children, symbol, weight, n_clicks)
    else:
        children = append_row(children, None, None, n_clicks)
    return children


def append_row(children, symbol, weight, n_clicks):
    new_row = dbc.Row(
        [
            dbc.Col(
                dcc.Dropdown(
                    multi=False,
                    id={"type": "pf-dynamic-dropdown", "index": n_clicks},
                    options=[symbol] if symbol else [],
                    value=symbol,
                    placeholder="Type a ticker",
                ),
            ),
            dbc.Col(
                dbc.Input(
                    id={"type": "pf-dynamic-input", "index": n_clicks},
                    placeholder="Type a weight",
                    value=weight,
                    type="number",
                    min=0,
                    max=100,
                )
            ),
        ]
    )
    children.append(new_row)
    return children


@app.callback(
    Output({"type": "pf-dynamic-dropdown", "index": MATCH}, "options"),
    Input({"type": "pf-dynamic-dropdown", "index": MATCH}, "search_value"),
)
def optimize_search_al(search_value) -> list:
    if not search_value:
        raise PreventUpdate
    return [o for o in options if re.match(search_value, o, re.IGNORECASE)]


@app.callback(
    Output("pf-portfolio-weights-sum", "children"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
)
def print_weights_sum(values) -> Tuple[str, bool]:
    weights_sum = sum(float(x) for x in values if x)
    weights_sum_is_not_100 = np.around(weights_sum, decimals=3) != 100.0
    return f"Total: {weights_sum}", weights_sum_is_not_100


@app.callback(
    Output("pf-submit-button", "disabled"),
    Output("pf-copy-link-button", "disabled"),
    Output("dynamic-add-filter", "disabled"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    Input("pf-rolling-window", "value"),
)
def disable_submit_add_link_buttons(tickers_list, weights_list, rolling_window_value) -> Tuple[bool, bool, bool]:
    """
    Disable "Add Asset", "Submit" and "Copy Link" buttons.

    disable "Add Asset" conditions:
    - weights and assets forms are not empty (don't have None)
    - number of tickers is more or equal than allowed (in settings)

    disable "Submit" conditions:
    - sum of weights is not 100
    - number of weights is not equal to the number of assets
    - rolling window size is natural number

    disable "Copy Link" conditions:
    - "Submit"
    - number of tickers is more than allowed (in settings)
    """
    add_condition1 = None in tickers_list or None in weights_list
    add_condition2 = len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS
    add_result = add_condition1 or add_condition2

    tickers_list = [i for i in tickers_list if i is not None]
    weights_list = [i for i in weights_list if i is not None]

    weights_sum = sum(float(x) for x in weights_list if x)
    weights_sum_is_not_100 = np.around(weights_sum, decimals=3) != 100.0

    weights_and_tickers_has_different_length = len(set(tickers_list)) != len(weights_list)
    rolling_not_natural = validators.validate_integer_bool(rolling_window_value)
    submit_result = weights_sum_is_not_100 or weights_and_tickers_has_different_length or rolling_not_natural

    link_condition = len(tickers_list) > settings.ALLOWED_NUMBER_OF_TICKERS
    link_result = submit_result or link_condition
    return submit_result, link_result, add_result

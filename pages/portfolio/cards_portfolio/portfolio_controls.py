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
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl

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
    # advanced
    initial_amount: Optional[float],
    cashflow: Optional[float],
    discount_rate: Optional[float],
    symbol: Optional[str],
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
                                    clearable=False,
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
                                    tl.pf_rebalancing_period,
                                    target="pf-info-rebalancing",
                                ),
                            ],
                            lg=6,
                            md=6,
                            sm=12,
                        ),
                    ]
                ),
                html.Div(
                    [
                        # Attributes
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
                        # Advanced attributes
                        dbc.Row(
                            [
                                dbc.Accordion(
                                    [
                                        dbc.AccordionItem(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    [
                                                                        "Initial amount",
                                                                        html.I(
                                                                            className="bi bi-info-square ms-2",
                                                                            id="pf-info-initial-amount",
                                                                        ),
                                                                    ]
                                                                ),
                                                                dbc.Input(
                                                                    id="pf-initial-amount",
                                                                    value=initial_amount if initial_amount else 1000,
                                                                    type="number",
                                                                    min=1,
                                                                ),
                                                                dbc.FormText("Positive number"),
                                                                dbc.Tooltip(
                                                                    tl.pf_options_tooltip_initial_amount,
                                                                    target="pf-info-initial-amount",
                                                                ),
                                                            ]
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    [
                                                                        "Monthly cash flow",
                                                                        html.I(
                                                                            className="bi bi-info-square ms-2",
                                                                            id="pf-info-cash-flow",
                                                                        ),
                                                                    ]
                                                                ),
                                                                dbc.Input(
                                                                    id="pf-cashflow",
                                                                    value=cashflow if cashflow else 0,
                                                                    type="number",
                                                                ),
                                                                dbc.FormText("Number"),
                                                                dbc.Tooltip(
                                                                    tl.pf_options_tooltip_cash_flow,
                                                                    target="pf-info-cash-flow",
                                                                ),
                                                            ],
                                                            lg=5,
                                                            md=5,
                                                            sm=12,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label("Rate"),
                                                                dbc.Input(
                                                                    id="pf-withdrawal-rate",
                                                                    disabled=True
                                                                ),
                                                                dbc.Tooltip(
                                                                    tl.pf_options_tooltip_cash_flow,
                                                                    target="pf-info-withdrawal-rate",
                                                                ),
                                                            ],
                                                            lg=2,
                                                            md=2,
                                                            sm=12,
                                                        ),
                                                    ]
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    [
                                                                        "Discount rate",
                                                                        html.I(
                                                                            className="bi bi-info-square ms-2",
                                                                            id="pf-info-discount-rate",
                                                                        ),
                                                                    ]
                                                                ),
                                                                dbc.Input(
                                                                    id="pf-discount-rate",
                                                                    type="number",
                                                                    min=0,
                                                                    max=1,
                                                                    value=discount_rate if discount_rate else None,
                                                                ),
                                                                dbc.FormText("0 - 1 (0.05 is equivalent to 5%)"),
                                                                dbc.Tooltip(
                                                                    tl.pf_options_tooltip_discount_rate,
                                                                    target="pf-info-discount-rate",
                                                                ),
                                                            ],
                                                            lg=5,
                                                            md=5,
                                                            sm=12,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.Label(
                                                                    [
                                                                        "Portfolio ticker",
                                                                        html.I(
                                                                            className="bi bi-info-square ms-2",
                                                                            id="pf-info-ticker",
                                                                        ),
                                                                    ]
                                                                ),
                                                                dbc.Input(
                                                                    id="pf-ticker",
                                                                    type="text",
                                                                    value=symbol if symbol else "PORTFOLIO",
                                                                ),
                                                                dbc.FormText("Symbols without spaces"),
                                                                dbc.Tooltip(
                                                                    tl.pf_options_tooltip_ticker,
                                                                    target="pf-info-ticker",
                                                                ),
                                                            ],
                                                            lg=5,
                                                            md=5,
                                                            sm=12,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            title="Advanced parameters",
                                        ),
                                    ],
                                    start_collapsed=True,
                                    flush=True,
                                    class_name="p-0",
                                )
                            ],
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
                        dbc.Row(
                            html.H5(children="Options"),
                            className="p-1",
                        ),
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
                                                {"label": "Distribution test", "value": "distribution"},
                                            ],
                                            value="wealth",
                                            id="pf-plot-option",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_options_tooltip_cagr,
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
                                            tl.pf_options_tooltip_inflation,
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
                                            tl.pf_options_window,
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
                        dbc.Row(
                            html.H6(children="Monte Carlo simulation for portfolio future wealth indexes"),
                            className="p-1",
                            id="pf-monte-carlo-header-row"
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    [
                                        "Random simulations number",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-info-monte-number-label",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_mc_tooltip_mc_number,
                                            target="pf-info-monte-number-label",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            type="number",
                                            value=0,
                                            id="pf-monte-carlo-number",
                                        ),
                                        dbc.FormFeedback("", type="valid"),
                                        dbc.FormFeedback(
                                            f"it should be an integer number ≤{settings.MC_PORTFOLIO_MAX}",
                                            type="invalid",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-number-row"
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    [
                                        "Forecast period",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-info-monte-carlo-years-label",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_mc_tooltip_forecast_period,
                                            target="pf-info-monte-carlo-years-label",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            type="number",
                                            min=1,
                                            max=100,
                                            value=10,
                                            id="pf-monte-carlo-years",
                                        ),
                                        dbc.FormFeedback("", type="valid"),
                                        dbc.FormFeedback(
                                            f"it should be an integer number ≤{settings.MC_EF_MAX}", type="invalid"
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-period-row"
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    [
                                        "Distribution type",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-monte-carlo-distribution-label",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_mc_tooltip_distribution,
                                            target="pf-monte-carlo-distribution-label",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dcc.Dropdown(
                                            options=[
                                                {"label": "Normal distribution", "value": "norm"},
                                                {"label": "Lognormal distribution", "value": "lognorm"},
                                            ],
                                            value="norm",
                                            multi=False,
                                            clearable=False,
                                            placeholder="Select a distribution type",
                                            id="pf-monte-carlo-distribution",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-distribution-row"
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    [
                                        "Include backtest",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-monte-carlo-backtest-label",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_mc_tooltip_backtest,
                                            target="pf-monte-carlo-backtest-label",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dcc.Dropdown(
                                            options=["yes", "no"],
                                            value="yes",
                                            multi=False,
                                            clearable=False,
                                            placeholder="Show backtest before Monte Carlo?",
                                            id="pf-monte-carlo-backtest",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-backtest-row"
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
def disable_rolling_input(plot_options: str) -> bool:
    return plot_options in {"wealth", "drawdowns", "distribution"}


@callback(
    Output(component_id="pf-monte-carlo-header-row", component_property="style"),
    Output(component_id="pf-monte-carlo-number-row", component_property="style"),
    Output(component_id="pf-monte-carlo-period-row", component_property="style"),
    Output(component_id="pf-monte-carlo-distribution-row", component_property="style"),
    Output(component_id="pf-monte-carlo-backtest-row", component_property="style"),
    Input(component_id="pf-plot-option", component_property="value"),
)
def hide_monte_carlo_rows(plot_options: str):
    style = {"display": "none"} if plot_options != "wealth" else None
    return tuple((style for i in range(0, 5)))


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
    # Advanced
    State("pf-initial-amount", "value"),
    State("pf-cashflow", "value"),
    State("pf-discount-rate", "value"),
    State("pf-ticker", "value"),
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
    # Advanced
    initial_amount: Optional[float],
    cashflow: Optional[float],
    discount_rate: Optional[float],
    symbol: Optional[str],
):
    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        weights_list=weights_list,
        rebal=rebal,
        # Advanced
        initial_amount=initial_amount,
        cashflow=cashflow,
        discount_rate=discount_rate,
        symbol=symbol,
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
    return f"Total: {np.around(weights_sum, decimals=3)}", weights_sum_is_not_100


@app.callback(
    Output("pf-withdrawal-rate", "value"),
    Input("pf-initial-amount", "value"),  #
    Input("pf-cashflow", "value")
)
def print_withdrawal_rate(initial_amount, cashflow) -> str:
    if initial_amount and cashflow:
        withdrawal_rate = abs(int(cashflow)) * settings.MONTHS_PER_YEAR / int(initial_amount) * 100
    else:
        withdrawal_rate = 0
    return f"{withdrawal_rate:.0f}%"


@app.callback(
    Output("pf-submit-button", "disabled"),
    Output("pf-copy-link-button", "disabled"),
    Output("dynamic-add-filter", "disabled"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    Input("pf-rolling-window", "value"),
    Input("pf-monte-carlo-number", "valid"),
)
def disable_submit_add_link_buttons(
    tickers_list, weights_list, rolling_window_value, mc_number_valid
) -> Tuple[bool, bool, bool]:
    """
    Disable "Add Asset", "Submit" and "Copy Link" buttons.

    disable "Add Asset" conditions:
    - weights and assets forms are not empty (don't have None)
    - number of tickers is more or equal than allowed (in settings)

    disable "Submit" conditions:
    - sum of weights is not 100
    - number of weights is not equal to the number of assets
    - rolling window size is natural number
    - MC number is valid

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

    mc_number_is_incorrect = mc_number_valid == False

    submit_result = (
        weights_sum_is_not_100
        or weights_and_tickers_has_different_length
        or rolling_not_natural
        or mc_number_is_incorrect
    )

    link_condition = len(tickers_list) > settings.ALLOWED_NUMBER_OF_TICKERS
    link_result = submit_result or link_condition
    return submit_result, link_result, add_result


@app.callback(
    Output("pf-monte-carlo-number", "valid"),
    Output("pf-monte-carlo-number", "invalid"),
    Input("pf-monte-carlo-number", "value"),
)
def check_validity_monte_carlo(number: int):
    """
    Check if input is an integer in range for 0 to MC_PORTFOLIO_MAX.
    """
    if number is not None:
        is_correct_number = number in range(0, settings.MC_PORTFOLIO_MAX + 1) and isinstance(number, int)
        return is_correct_number, not is_correct_number
    return False, False

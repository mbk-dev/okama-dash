import re
from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback

import pandas as pd

from common import settings as settings, inflation as inflation
from common.create_link import create_link, check_if_list_empty_or_big
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import make_list_from_string
from common.symbols import get_symbols
from common import cache
import common.validators as validators
from pages.compare.cards_compare.eng.al_tooltips_options_txt import (
    al_options_tooltip_inflation,
    al_options_tooltip_cagr,
    al_options_window,
)

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
    tickers_list = make_list_from_string(tickers)
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Compare Assets", className="card-title"),
                html.Div(
                    [
                        html.Label("Tickers to compare"),
                        dcc.Dropdown(
                            options=options,
                            value=tickers_list if tickers_list else settings.default_symbols,
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
                        dbc.Row(html.H5("Options")),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Plot:",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="al-info-plot",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "Wealth Index", "value": "wealth"},
                                                {"label": "Rolling Cagr", "value": "cagr"},
                                                {"label": "Rolling Real Cagr", "value": "real_cagr"},
                                                {"label": "Correlation matrix", "value": "correlation"},
                                            ],
                                            value="wealth",
                                            id="al-plot-option",
                                        ),
                                        dbc.Tooltip(
                                            al_options_tooltip_cagr,
                                            target="al-info-plot",
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
                                                    id="al-info-inflation",
                                                ),
                                            ]
                                        ),
                                        dbc.Switch(
                                            label="",
                                            value=False,
                                            id="al-inflation-switch",
                                        ),
                                        dbc.Tooltip(
                                            al_options_tooltip_inflation,
                                            target="al-info-inflation",
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
                                                    id="al-info-rolling",
                                                ),
                                            ]
                                        ),
                                        dbc.Input(
                                            type="number",
                                            min=1,
                                            value=2,
                                            id="al-rolling-window",
                                        ),
                                        dbc.FormText("Format: number of years (≥ 1)"),
                                        dbc.Tooltip(
                                            al_options_window,
                                            target="al-info-rolling",
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
    Output(component_id="al-rolling-window", component_property="disabled"),
    Input(component_id="al-plot-option", component_property="value"),
)
def update_rolling_input(plot_options: str):
    return plot_options in {"wealth", "correlation"}


@callback(
    Output(component_id="al-inflation-switch", component_property="value"),
    Output(component_id="al-inflation-switch", component_property="disabled"),
    Input(component_id="al-plot-option", component_property="value"),
    State(component_id="al-inflation-switch", component_property="value"),
)
def update_inflation_switch(plot_options: str, inflation_switch_value):
    """
    Change inflation-switch value and disabled state.

    It should be "ON" and "Disabled" if "Real CAGR" chart selected.
    """
    if plot_options == "real_cagr":
        return True, True
    else:
        return inflation_switch_value, False


@callback(
    Output("al-show-url", "children"),
    Input("al-copy-link-button", "n_clicks"),
    State("al-url", "href"),
    State("al-symbols-list", "value"),  # get selected tickers
    State("al-base-currency", "value"),
    State("al-first-date", "value"),
    State("al-last-date", "value"),
    prevent_initial_call=True,
)
def update_link_al(n_clicks, href: str, tickers_list: Optional[list], ccy: str, first_date: str, last_date: str):
    return create_link(ccy=ccy, first_date=first_date, href=href, last_date=last_date, tickers_list=tickers_list)


@app.callback(
    Output("al-symbols-list", "options"),
    Input("al-symbols-list", "search_value"),
    Input("al-symbols-list", "value"),
)
def optimize_search_al(search_value, selected_values):
    return (
        [o for o in options if re.match(search_value, o, re.IGNORECASE) or o in (selected_values or [])]
        if search_value
        else selected_values
    )


@app.callback(
    Output("al-logarithmic-scale-switch-div", "hidden"),
    Input(component_id="al-submit-button", component_property="n_clicks"),
    State(component_id="al-plot-option", component_property="value"),
)
def show_log_scale_switch(n_clicks, plot_type: str):
    return plot_type not in ("wealth",)


@app.callback(
    Output("al-symbols-list", "disabled"),
    Input("al-symbols-list", "value"),
)
def disable_search(tickers_list) -> bool:
    """
    Disable asset search form if the number of ticker exceeds allowed in settings.
    """
    return len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS


@app.callback(
    Output("al-copy-link-button", "disabled"),
    Input("al-symbols-list", "value"),
)
def disable_link_button(tickers_list) -> bool:
    """
    Disable "Copy Link" button.

    Conditions:
    - list of tickers is empty
    - number of tickers is more than allowed (in settings)
    """
    return check_if_list_empty_or_big(tickers_list)


@app.callback(
    Output("al-submit-button", "disabled"), Input("al-symbols-list", "value"), Input("al-rolling-window", "value")
)
def disable_submit(tickers_list, rolling_window_value) -> bool:
    """
    Disable "Compare" (Submit) button.

    conditions:
    - number of tickers is 0
    - rolling window size is not natural
    """
    if not tickers_list:
        return True
    no_tickers = len(tickers_list) == 0
    rolling_not_natural = validators.validate_integer_bool(rolling_window_value)
    return no_tickers or rolling_not_natural

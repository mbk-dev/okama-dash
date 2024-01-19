import re
from typing import Optional

import dash
import dash.exceptions
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
from pages.benchmark.cards_benchmark.eng.benchmark_tooltips_options_txt import (
    benchmark_options_tooltip_plot,
    benchmark_options_tooltip_window_size,
    benchmark_options_tooltip_type,
)

app = dash.get_app()
cache.init_app(app.server)
options = get_symbols()

today_str = pd.Timestamp.today().strftime("%Y-%m")


def benchmark_card_controls(
    benchmark: Optional[str],
    tickers: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
):
    tickers_list = make_list_from_string(tickers)
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Compare with Benchmark", className="card-title"),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Benchmark"),
                                        dcc.Dropdown(
                                            options=options,
                                            multi=False,
                                            placeholder="Select a benchmark",
                                            id="select-benchmark",
                                            value=benchmark if benchmark else settings.default_benchmark,
                                        ),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=12,
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Tickers to compare with benchmark"),
                        dcc.Dropdown(
                            options=options,
                            value=tickers_list if tickers_list else settings.default_symbols_benchmark,
                            multi=True,
                            placeholder="Select tickers",
                            id="benchmark-assets-list",
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Label("Base currency"),
                        dcc.Dropdown(
                            options=inflation.get_currency_list(),
                            value=ccy if ccy else settings.default_currency,
                            multi=False,
                            placeholder="Select a base currency",
                            id="benchmark-base-currency",
                        ),
                    ],
                ),
                html.Div(
                    id="benchmark-options-div",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("First Date"),
                                        dbc.Input(
                                            id="benchmark-first-date",
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
                                            id="benchmark-last-date",
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
                                location_id="benchmark-url",
                                hidden_div_with_url_id="benchmark-show-url",
                                button_id="benchmark-copy-link-button",
                                card_name="widget",
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
                                                    id="benchmark-info-plot",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "Tracking difference", "value": "td"},
                                                {"label": "Annualized Tracking difference", "value": "annualized_td"},
                                                {
                                                    "label": "Annual Tracking difference (bars)",
                                                    "value": "annual_td_bar",
                                                },
                                                {"label": "Tracking Error", "value": "te"},
                                                {"label": "Correlation", "value": "correlation"},
                                                {"label": "Beta coefficient", "value": "beta"},
                                            ],
                                            value="annualized_td",
                                            id="benchmark-plot-option",
                                        ),
                                        dbc.Tooltip(
                                            benchmark_options_tooltip_plot,
                                            target="benchmark-info-plot",
                                        ),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Chart Type:",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="benchmark-info-chart-type",
                                                ),
                                            ]
                                        ),
                                        dbc.Tooltip(
                                            benchmark_options_tooltip_type,
                                            target="benchmark-info-chart-type",
                                        ),
                                        dbc.RadioItems(
                                            options=[
                                                {"label": "Expanding", "value": "expanding"},
                                                {"label": "Rolling", "value": "rolling"},
                                            ],
                                            value="expanding",
                                            id="benchmark-chart-expanding-rolling",
                                        ),
                                        dbc.Label(
                                            [
                                                "Rolling Window",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="benchmark-info-rolling",
                                                ),
                                            ]
                                        ),
                                        dbc.Input(
                                            type="number",
                                            min=1,
                                            value=2,
                                            id="benchmark-rolling-window",
                                        ),
                                        dbc.FormText("Format: number of years (≥ 1)"),
                                        dbc.Tooltip(
                                            benchmark_options_tooltip_window_size,
                                            target="benchmark-info-rolling",
                                        ),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                            ]
                        ),
                    ],
                ),
                html.Div(
                    [
                        dbc.Button(
                            children="Compare",
                            id="benchmark-submit-button",
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
    Output("benchmark-rolling-window", "disabled"),
    Input("benchmark-plot-option", "value"),
    Input("benchmark-chart-expanding-rolling", "value"),
)
def disable_rolling_input(plot_options: str, expanding_rolling):
    condition1 = expanding_rolling == "expanding"
    condition2 = plot_options == "annual_td_bar"
    return condition1 or condition2


@callback(
    Output("benchmark-chart-expanding-rolling", "options"),
    Output("benchmark-chart-expanding-rolling", "value"),
    Input("benchmark-plot-option", "value"),
    Input("benchmark-chart-expanding-rolling", "value"),
)
def disable_rolling_expanding_switch(plot_options: str, radio_switch_value):
    disabled = plot_options == "annual_td_bar"
    radio_options = [
        {"label": "Expanding", "value": "expanding"},
        {"label": "Rolling", "value": "rolling", "disabled": disabled},
    ]
    new_value = "expanding" if disabled else radio_switch_value
    return radio_options, new_value


@callback(
    Output("benchmark-show-url", "children"),
    Input("benchmark-copy-link-button", "n_clicks"),
    State("benchmark-url", "href"),
    State("select-benchmark", "value"),  # benchmark
    State("benchmark-assets-list", "value"),  # selected tickers
    State("benchmark-base-currency", "value"),
    State("benchmark-first-date", "value"),
    State("benchmark-last-date", "value"),
)
def update_link_benchmark(
    n_clicks, href: str, benchmark: str, tickers_list: list, ccy: str, first_date: str, last_date: str
):
    return create_link(
        ccy=ccy, first_date=first_date, href=href, last_date=last_date, tickers_list=tickers_list, benchmark=benchmark
    )


@app.callback(
    Output("select-benchmark", "options"),
    Input("select-benchmark", "search_value"),
    Input("select-benchmark", "value"),
)
def optimize_search_benchmark(search_value, selected_value):
    if not search_value:
        raise dash.exceptions.PreventUpdate
    return [o for o in options if re.match(search_value, o, re.IGNORECASE)] if search_value else selected_value


@app.callback(
    Output("benchmark-assets-list", "options"),
    Input("benchmark-assets-list", "search_value"),
    Input("benchmark-assets-list", "value"),
)
def optimize_search_assets_benchmark(search_value, selected_values):
    return (
        [o for o in options if re.match(search_value, o, re.IGNORECASE) or o in (selected_values or [])]
        if search_value
        else selected_values
    )


@app.callback(
    Output("benchmark-assets-list", "disabled"),
    Input("benchmark-assets-list", "value"),
)
def disable_search(tickers_list) -> bool:
    """
    Disable asset search form if the number of ticker exceeds allowed in settings.
    """
    return len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS


@app.callback(
    Output("benchmark-copy-link-button", "disabled"),
    Input("benchmark-assets-list", "value"),
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
    Output("benchmark-submit-button", "disabled"),
    Input("benchmark-assets-list", "value"),
    Input("benchmark-rolling-window", "value"),
)
def disable_submit(tickers_list, rolling_window_value) -> bool:
    """
    Disable "Compare" (Submit) button.

    conditions:
    - number of tickers is 0
    - rolling_window is not Natural number
    """
    condition1 = len(tickers_list) == 0
    condition2 = validators.validate_integer_bool(rolling_window_value)
    return condition1 or condition2

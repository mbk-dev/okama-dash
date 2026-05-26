from typing import Optional

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, callback
from dash.dependencies import Input, Output

import pandas as pd

from common import settings as settings, inflation as inflation
from common.mantine import search_provider
from common.create_link import create_link, check_if_list_empty_or_big
from common.html_elements.copy_link_div import create_copy_link_div
from common.symbols import get_selected_symbol_options, search_symbol_options
from common import cache
from common.date_input import date_input, register_date_validation
import pages.efficient_frontier.cards_efficient_frontier.eng.ef_tooltips_options_txt as tl

app = dash.get_app()
cache.init_app(app.server)

today_str = pd.Timestamp.today().strftime("%Y-%m")

PLOT_OPTIONS = [
    {
        "label": "Efficient frontier",
        "value": "Frontier",
    },
    {
        "label": "Pairwise efficiency frontiers",
        "value": "Pairwise",
    },
]

RETURN_TYPE_OPTIONS = [
    {"label": "Geometric mean", "value": "Geometric"},
    {"label": "Arithmetic mean", "value": "Arithmetic"},
]

TOGGLE_OPTIONS = [
    {"label": "On", "value": "On"},
    {"label": "Off", "value": "Off"},
]


def _normalize_plot_types(plot_type) -> list[str]:
    if plot_type is None:
        return []
    if isinstance(plot_type, str):
        return [plot_type]
    return list(dict.fromkeys(plot_type))


def _get_plot_options(pairwise_disabled: bool) -> list[dict]:
    result = []
    for option in PLOT_OPTIONS:
        current_option = option.copy()
        if current_option["value"] == "Pairwise":
            current_option["disabled"] = pairwise_disabled
        result.append(current_option)
    return result


def _get_toggle_options(disabled: bool) -> list[dict]:
    return [dict(option, disabled=disabled) for option in TOGGLE_OPTIONS]


def card_controls(
    tickers: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
    rebal: Optional[str],
):
    rebal_options = {"year", "half-year", "quarter", "month", "none"}
    rebal_from_url = rebal.lower() if isinstance(rebal, str) else None
    rebal_value = rebal_from_url if rebal_from_url in rebal_options else "month"

    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Efficient Frontier", className="card-title"),
                html.Div(
                    [
                        html.Label("Tickers in the Efficient Frontier"),
                        search_provider(
                            dmc.MultiSelect(
                                data=get_selected_symbol_options(tickers if tickers else settings.default_symbols),
                                value=tickers if tickers else settings.default_symbols,
                                placeholder="Select assets",
                                id="ef-symbols-list",
                                searchable=True,
                                clearable=False,
                                nothingFoundMessage="No matching tickers",
                                comboboxProps={"shadow": "md"},
                            )
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
                            clearable=False,
                            placeholder="Select a base currency",
                            id="ef-base-currency",
                        ),
                        html.Label("Rebalancing Frequency"),
                        dcc.Dropdown(
                            options=[
                                {"label": "year", "value": "year"},
                                {"label": "half-year", "value": "half-year"},
                                {"label": "quarter", "value": "quarter"},
                                {"label": "month", "value": "month"},
                                {"label": "none", "value": "none"},
                            ],
                            value=rebal_value,
                            multi=False,
                            clearable=False,
                            placeholder="Select rebalancing frequency",
                            id="ef-rebalancing-frequency",
                        ),
                    ],
                ),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [html.Label("First Date")]
                                    + date_input("ef-first-date", first_date if first_date else "2000-01"),
                                ),
                                dbc.Col(
                                    [html.Label("Last Date")]
                                    + date_input("ef-last-date", last_date if last_date else today_str),
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
                                                "Plot:",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-ror",
                                                ),
                                            ]
                                        ),
                                        dbc.Checklist(
                                            options=PLOT_OPTIONS,
                                            value=["Frontier"],
                                            id="ef-plot-options",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_ror,
                                            target="info-ror",
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
                                                "Y-axis",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-mean-type",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=RETURN_TYPE_OPTIONS,
                                            value="Geometric",
                                            id="ef-mean-type-option",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_mean_type,
                                            target="info-mean-type",
                                        ),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                            ],
                            className="p-1",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            [
                                                "Most diversified portfolios line",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-mdp-line",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=TOGGLE_OPTIONS,
                                            value="Off",
                                            id="mdp-line-option",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_mdp,
                                            target="info-mdp-line",
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
                                                "Capital Market Line (CML)",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="info-cml",
                                                ),
                                            ]
                                        ),
                                        dbc.RadioItems(
                                            options=TOGGLE_OPTIONS,
                                            value="Off",
                                            id="cml-option",
                                        ),
                                        dbc.Tooltip(
                                            tl.ef_options_tooltip_cml,
                                            target="info-cml",
                                        ),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                            ],
                            className="p-1",
                        ),
                        dbc.Row(
                            [
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
                                    lg=6,
                                    md=6,
                                    sm=12,
                                    class_name="pt-4 pt-sm-4 pt-md-1",
                                ),
                                dbc.Col(lg=6, md=6, sm=12),
                            ],
                            className="p-1",
                        ),
                        dbc.Row(html.H6(children="Monte Carlo Simulation")),
                        dbc.Row(
                            [
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
                                            value=0,
                                            id="monte-carlo-option",
                                        ),
                                        dbc.FormFeedback("", type="valid"),
                                        dbc.FormFeedback(
                                            f"it should be an integer number ≤{settings.MC_EF_MAX}", type="invalid"
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Tooltip(
                                    tl.ef_options_monte_carlo,
                                    target="info-monte-carlo",
                                ),
                            ],
                            className="p-1",
                        ),
                        dbc.Row(html.H6(children="Transition map")),
                        dbc.Row(
                            [
                                dbc.Label(
                                    [
                                        "Show transition map",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="info-transition-map",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Tooltip(
                                    tl.ef_options_transition_map,
                                    target="info-transition-map",
                                ),
                                dbc.RadioItems(
                                    options=[
                                        {"label": "On", "value": "On"},
                                        {"label": "Off", "value": "Off"},
                                    ],
                                    value="Off",
                                    id="transition-map-option",
                                ),
                            ],
                            className="p-1",
                        ),
                    ]
                ),
                html.Div(
                    [
                        dbc.Button(
                            children="Submit",
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
    Output("ef-plot-options", "options"),
    Output("ef-plot-options", "value"),
    Output("mdp-line-option", "options"),
    Output("mdp-line-option", "value"),
    Output("cml-option", "options"),
    Output("cml-option", "value"),
    Output("monte-carlo-option", "disabled"),
    Output("monte-carlo-option", "value"),
    Input("ef-plot-options", "value"),
    Input("ef-mean-type-option", "value"),
    Input("mdp-line-option", "value"),
    Input("cml-option", "value"),
    Input("monte-carlo-option", "value"),
)
def sync_incompatible_options(plot_type, mean_type_value, mdp_value, cml_value, monte_carlo_value):
    plot_types = _normalize_plot_types(plot_type)
    mean_type_value = mean_type_value or "Geometric"
    mdp_value = mdp_value or "Off"
    cml_value = cml_value or "Off"
    monte_carlo_value = 0 if monte_carlo_value is None else monte_carlo_value
    triggered_id = dash.ctx.triggered_id

    incompatible_selected = mdp_value == "On" or cml_value == "On" or monte_carlo_value > 0
    pairwise_selected = "Pairwise" in plot_types

    if triggered_id in {"mdp-line-option", "cml-option", "monte-carlo-option"} and incompatible_selected:
        plot_types = [option for option in plot_types if option != "Pairwise"]
        pairwise_selected = False

    if triggered_id == "ef-plot-options" and pairwise_selected:
        mdp_value = "Off"
        cml_value = "Off"
        monte_carlo_value = 0
        incompatible_selected = False

    if not plot_types:
        plot_types = ["Frontier"]

    pairwise_selected = "Pairwise" in plot_types
    # TODO: remove Arithmetic-based MDP/CML disabling after EfficientFrontier in okama
    # supports correct Mean return vs CAGR handling for MDP and CML.
    mdp_cml_disabled = pairwise_selected or mean_type_value == "Arithmetic"

    if mdp_cml_disabled:
        mdp_value = "Off"
        cml_value = "Off"

    if pairwise_selected:
        monte_carlo_value = 0

    pairwise_disabled = mdp_value == "On" or cml_value == "On" or monte_carlo_value > 0

    return (
        _get_plot_options(pairwise_disabled=pairwise_disabled),
        plot_types,
        _get_toggle_options(disabled=mdp_cml_disabled),
        mdp_value,
        _get_toggle_options(disabled=mdp_cml_disabled),
        cml_value,
        pairwise_selected,
        monte_carlo_value,
    )


@callback(
    Output("ef-show-url", "children"),
    Input("ef-url", "href"),
    Input("ef-symbols-list", "value"),
    Input("ef-base-currency", "value"),
    Input("ef-first-date", "value"),
    Input("ef-last-date", "value"),
    Input("ef-rebalancing-frequency", "value"),
)
def update_link_ef(href: str, tickers_list: list, ccy: str, first_date: str, last_date: str, rebal: str):
    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        rebal=rebal,
    )


@app.callback(
    Output("ef-symbols-list", "data"),
    Input("ef-symbols-list", "searchValue"),
    Input("ef-symbols-list", "value"),
)
def optimize_search_ef(search_value, selected_values):
    return search_symbol_options(search_value, selected_values)


@app.callback(
    Output("monte-carlo-option", "valid"),
    Output("monte-carlo-option", "invalid"),
    Input("monte-carlo-option", "value"),
)
def check_validity_monte_carlo(number: int):
    """
    Check if input is an integer in range for 0 to MC_MAX.
    """
    if number is not None:
        is_correct_number = number in range(0, settings.MC_EF_MAX + 1) and isinstance(number, int)
        return is_correct_number, not is_correct_number
    return False, False


@app.callback(
    Output("ef-symbols-list", "disabled"),
    Input("ef-symbols-list", "value"),
)
def disable_search(tickers_list) -> bool:
    """
    Disable asset search form if the number of ticker exceeds allowed in settings.
    """
    return len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS


@app.callback(
    Output("ef-copy-link-button", "disabled"),
    Input("ef-symbols-list", "value"),
)
def disable_link_button(tickers_list) -> bool:
    """
    Disable "Copy Link" button.

    Conditions:
    - list of tickers length is < 2
    - number of tickers is more than allowed (in settings)
    """
    return check_if_list_empty_or_big(tickers_list) or len(tickers_list) < 2


@app.callback(
    Output("ef-submit-button-state", "disabled"),
    Input("ef-symbols-list", "value"),
    Input("monte-carlo-option", "valid"),
)
def disable_submit(tickers_list, mc_number_valid) -> bool:
    """
    Disable Submit button.

    conditions:
    - number of tickers is < 2
    - MC number is incorrect
    """
    number_of_tickers_is_too_small = len(tickers_list) < 2
    mc_number_is_incorrect = mc_number_valid == False

    submit_result = number_of_tickers_is_too_small or mc_number_is_incorrect
    return submit_result


register_date_validation("ef-first-date")
register_date_validation("ef-last-date")

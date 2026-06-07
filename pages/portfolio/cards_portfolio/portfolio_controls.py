"""
test URL:
http://127.0.0.1:8050/portfolio?tickers=SPY.US,BND.US,GLD.US&weights=30,20,50&first_date=2015-01&last_date=2020-12&ccy=RUB&rebal=year
"""

from typing import Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback, ALL, MATCH

import pandas as pd
from dash.exceptions import PreventUpdate

from common import settings as settings, inflation as inflation
from common.html_elements.submit_spinner import create_submit_spinner
from common.mantine import search_provider
from common.create_link import create_link, scope_cashflow_params
from common.html_elements.copy_link_div import create_copy_link_div
from common.parse_query import make_list_from_string
from common.symbols import get_selected_symbol_options, search_symbol_options
import common.validators as validators
from common.date_input import date_input, register_date_validation
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl
from pages.portfolio.cards_portfolio.rebalancing_controls import rebalancing_accordion_item
from pages.portfolio.cards_portfolio.cashflow_controls import cashflow_accordion_item


today_str = pd.Timestamp.today().strftime("%Y-%m")


def _accordion_active_items(abs_dev, rel_dev, cf_strategy, cf_amount, cf_pct, vds_pct, cwd_amount, cf_ts):
    active = []
    if abs_dev is not None or rel_dev is not None:
        active.append("rebalancing")
    has_cf = (
        (cf_strategy is not None and cf_strategy != "indexation")
        or (cf_amount is not None and cf_amount != 0)
        or (cf_pct is not None and cf_pct != 0)
        or vds_pct is not None
        or (cwd_amount is not None and cwd_amount != 0)
        or cf_ts is not None
    )
    if has_cf:
        active.append("cashflow")
    return active or []


def _mc_param_row(label_text, input_id, *, value=None, disabled=False, help_text=None):
    """One Label | numeric-Input row for a Monte Carlo distribution parameter."""
    label_children = [label_text]
    if help_text:
        label_children.append(html.Small(f" ({help_text})", className="text-muted"))
    return dbc.Row(
        [
            dbc.Label(label_children, width=6),
            dbc.Col(
                dbc.Input(type="number", value=value, disabled=disabled, id=input_id),
                width=6,
            ),
        ],
    )


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
    # rebalancing deviation
    abs_dev: Optional[float] = None,
    rel_dev: Optional[float] = None,
    # cashflow strategy
    cf_strategy: Optional[str] = None,
    cf_freq: Optional[str] = None,
    cf_amount: Optional[float] = None,
    cf_indexation: Optional[float] = None,
    cf_pct: Optional[float] = None,
    vds_pct: Optional[float] = None,
    vds_min: Optional[float] = None,
    vds_max: Optional[float] = None,
    vds_adj_mm: Optional[bool] = None,
    vds_floor: Optional[float] = None,
    vds_ceil: Optional[float] = None,
    vds_adj_fc: Optional[bool] = None,
    vds_indexation: Optional[float] = None,
    cwd_amount: Optional[float] = None,
    cwd_indexation: Optional[float] = None,
    # parsed CSV pairs: list of (str, str) tuples or None
    cwd_tr: Optional[list] = None,
    cf_ts: Optional[list] = None,
):
    tickers_list = make_list_from_string(tickers, char_type="str")
    weights_list = make_list_from_string(weights, char_type="float")
    currency_list = inflation.get_currency_list()
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Investment Portfolio", className="card-title"),
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Label("Tickers"), width=6),
                                dbc.Col(html.Label("Weights"), width=6),
                            ],
                        ),
                        html.Div(id="dynamic-container", children=[], className="vstack gap-2"),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Button("Add Asset", id="dynamic-add-filter", n_clicks=0)),
                                dbc.Col(html.Div(id="pf-portfolio-weights-sum")),
                            ]
                        ),
                    ],
                    className="vstack gap-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Base currency"),
                                dcc.Dropdown(
                                    options=currency_list,
                                    # URL values are normalized and validated: dcc.Dropdown
                                    # silently clears a value missing from its options.
                                    value=inflation.resolve_url_currency(ccy, currency_list),
                                    multi=False,
                                    clearable=False,
                                    placeholder="Select a base currency",
                                    id="pf-base-currency",
                                ),
                            ],
                        ),
                    ]
                ),
                html.Div(
                    [
                        # Attributes
                        dbc.Row(
                            [
                                dbc.Col(
                                    [html.Label("First Date")]
                                    + date_input("pf-first-date", first_date if first_date else "2000-01")
                                ),
                                dbc.Col(
                                    [html.Label("Last Date")]
                                    + date_input("pf-last-date", last_date if last_date else today_str)
                                ),
                            ]
                        ),
                        # Rebalancing & Cash Flow Strategy
                        dbc.Row(
                            [
                                dbc.Accordion(
                                    [
                                        rebalancing_accordion_item(
                                            rebal=rebal,
                                            abs_dev=abs_dev,
                                            rel_dev=rel_dev,
                                        ),
                                        cashflow_accordion_item(
                                            initial_amount=initial_amount,
                                            cashflow=cashflow,
                                            discount_rate=discount_rate,
                                            cf_strategy=cf_strategy,
                                            cf_freq=cf_freq,
                                            cf_amount=cf_amount,
                                            cf_indexation=cf_indexation,
                                            cf_pct=cf_pct,
                                            vds_pct=vds_pct,
                                            vds_min=vds_min,
                                            vds_max=vds_max,
                                            vds_adj_mm=vds_adj_mm,
                                            vds_floor=vds_floor,
                                            vds_ceil=vds_ceil,
                                            vds_adj_fc=vds_adj_fc,
                                            vds_indexation=vds_indexation,
                                            cwd_amount=cwd_amount,
                                            cwd_indexation=cwd_indexation,
                                            cwd_tr=cwd_tr,
                                            cf_ts=cf_ts,
                                        ),
                                    ],
                                    active_item=_accordion_active_items(
                                        abs_dev=abs_dev,
                                        rel_dev=rel_dev,
                                        cf_strategy=cf_strategy,
                                        cf_amount=cf_amount,
                                        cf_pct=cf_pct,
                                        vds_pct=vds_pct,
                                        cwd_amount=cwd_amount,
                                        cf_ts=cf_ts,
                                    ),
                                    flush=True,
                                    class_name="p-0",
                                    always_open=True,
                                )
                            ],
                        ),
                        # Portfolio ticker — a portfolio identity attribute (okama symbol),
                        # not a cash-flow parameter; kept outside the accordion so it stays
                        # visible even when the Cash Flow Strategy accordion is collapsed.
                        dbc.Row(
                            [
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
                                    lg=6,
                                    md=6,
                                    sm=12,
                                ),
                            ],
                            class_name="mt-2 mb-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    # copy link to clipboard button
                                    create_copy_link_div(
                                        location_id="pf-url",
                                        hidden_div_with_url_id="pf-show-url",
                                        button_id="pf-copy-link-button",
                                        card_name="Portfolio",
                                        # style={"textAlign": "right"}
                                    ),
                                ),
                            ]
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
                                                {"label": "Cumulative return", "value": "cumulative_return"},
                                                {"label": "Annual Return", "value": "annual_return"},
                                                {"label": "Rolling CAGR", "value": "cagr"},
                                                {"label": "Rolling Real CAGR", "value": "real_cagr"},
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
                            html.H6(children="Monte Carlo simulation"), className="p-1", id="pf-monte-carlo-header-row"
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
                                            f"it should be an integer number ≤{settings.MC_PORTFOLIO_MAX}, "
                                            f"and number × years ≤ {settings.MC_PORTFOLIO_BUDGET}",
                                            type="invalid",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-number-row",
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
                                            max=settings.MC_PORTFOLIO_YEARS_MAX,
                                            value=10,
                                            id="pf-monte-carlo-years",
                                        ),
                                        dbc.FormFeedback("", type="valid"),
                                        dbc.FormFeedback(
                                            f"it should be an integer number 1–{settings.MC_PORTFOLIO_YEARS_MAX}, "
                                            f"and number × years ≤ {settings.MC_PORTFOLIO_BUDGET}",
                                            type="invalid",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-period-row",
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
                                                {"label": "Student's t distribution", "value": "t"},
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
                            id="pf-monte-carlo-distribution-row",
                        ),
                        dbc.Row(
                            [
                                html.Div(
                                    [
                                        html.I(className="bi bi-chevron-right me-2", id="pf-mc-params-chevron"),
                                        "Distribution parameters",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="pf-mc-params-info-label",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_mc_tooltip_distribution_parameters,
                                            target="pf-mc-params-info-label",
                                        ),
                                    ],
                                    id="pf-mc-params-toggle",
                                    n_clicks=0,
                                    className="fw-bold",
                                    style={"cursor": "pointer", "userSelect": "none"},
                                ),
                                dbc.Collapse(
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    _mc_param_row("Mean (μ)", "pf-mc-norm-mu", value=None),
                                                    _mc_param_row(
                                                        "Std deviation (σ)",
                                                        "pf-mc-norm-sigma",
                                                        value=None,
                                                    ),
                                                ],
                                                id="pf-mc-norm-group",
                                                className="vstack gap-2",
                                            ),
                                            html.Div(
                                                [
                                                    _mc_param_row("Shape", "pf-mc-lognorm-shape", value=None),
                                                    _mc_param_row(
                                                        "Location (loc)",
                                                        "pf-mc-lognorm-loc",
                                                        value=-1,
                                                        disabled=True,
                                                        help_text="fixed at -1 by okama",
                                                    ),
                                                    _mc_param_row("Scale", "pf-mc-lognorm-scale", value=None),
                                                ],
                                                id="pf-mc-lognorm-group",
                                                className="vstack gap-2",
                                                style={"display": "none"},
                                            ),
                                            html.Div(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Label("Degrees of freedom (df)", width=6),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Input(
                                                                        type="number",
                                                                        value=None,
                                                                        id="pf-mc-t-df",
                                                                    ),
                                                                    dbc.FormFeedback("df must be > 2", type="invalid"),
                                                                ],
                                                                width=6,
                                                            ),
                                                        ],
                                                    ),
                                                    _mc_param_row("Location (loc)", "pf-mc-t-loc", value=None),
                                                    _mc_param_row("Scale (scale)", "pf-mc-t-scale", value=None),
                                                    dbc.Row(
                                                        [
                                                            dbc.Label(
                                                                [
                                                                    "VaR level, %",
                                                                    html.I(
                                                                        className="bi bi-info-square ms-2",
                                                                        id="pf-mc-var-level-info-label",
                                                                    ),
                                                                    dbc.Tooltip(
                                                                        tl.pf_mc_tooltip_var_level,
                                                                        target="pf-mc-var-level-info-label",
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                dbc.Input(
                                                                    type="number",
                                                                    min=1,
                                                                    max=99,
                                                                    value=None,
                                                                    placeholder="e.g. 5",
                                                                    id="pf-mc-t-var-level",
                                                                ),
                                                                width=6,
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                id="pf-mc-t-group",
                                                className="vstack gap-2",
                                                style={"display": "none"},
                                            ),
                                            html.Small(
                                                "", id="pf-mc-params-message", className="text-muted d-block mt-1"
                                            ),
                                        ],
                                        className="vstack gap-2 p-2",
                                    ),
                                    id="pf-mc-params-collapse",
                                    is_open=False,
                                ),
                            ],
                            class_name="pt-2",
                            id="pf-monte-carlo-params-row",
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
                            id="pf-monte-carlo-backtest-row",
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
                        dbc.DropdownMenu(
                            label="Go to",
                            id="pf-goto-menu",
                            # Outline look to match the previous Go to EF button:
                            # DropdownMenu has no outline prop, the toggle takes
                            # the class directly. d-inline-block keeps the menu
                            # wrapper on the Submit line (its default div is block).
                            toggle_class_name="btn-outline-primary",
                            class_name="d-inline-block ms-2",
                            children=[
                                dbc.DropdownMenuItem(
                                    "Efficient Frontier", id="pf-goto-ef", external_link=True, target="_blank"
                                ),
                                dbc.DropdownMenuItem(
                                    "Compare Assets", id="pf-goto-compare", external_link=True, target="_blank"
                                ),
                                dbc.DropdownMenuItem(
                                    "Benchmark", id="pf-goto-benchmark", external_link=True, target="_blank"
                                ),
                            ],
                        ),
                        create_submit_spinner("pf-submit-spinner"),
                    ],
                    style={"textAlign": "center"},
                    className="p-3",
                ),
                dcc.Store(id="pf_tickers_url", data=tickers_list),
                dcc.Store(id="pf_weights_url", data=weights_list),
                dcc.Store(id="pf_saved_portfolios_file_names", storage_type="session"),
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
    return plot_options in {"wealth", "cumulative_return", "drawdowns", "distribution", "annual_return"}


@callback(
    Output(component_id="pf-monte-carlo-header-row", component_property="style"),
    Output(component_id="pf-monte-carlo-number-row", component_property="style"),
    Output(component_id="pf-monte-carlo-period-row", component_property="style"),
    Output(component_id="pf-monte-carlo-distribution-row", component_property="style"),
    Output(component_id="pf-monte-carlo-params-row", component_property="style"),
    Output(component_id="pf-monte-carlo-backtest-row", component_property="style"),
    Input(component_id="pf-plot-option", component_property="value"),
    Input(component_id="pf-monte-carlo-number", component_property="value"),
)
def hide_monte_carlo_rows(plot_options: str, random_simulations_number):
    if plot_options != "wealth":
        # don't show rows
        style = {"display": "none"}
        return (style,) * 6
    else:
        if random_simulations_number in [0, None]:
            hidden = {"display": "none"}
            return None, None, hidden, hidden, hidden, hidden
        else:
            return (None,) * 6


@callback(
    Output(component_id="pf-mc-norm-group", component_property="style"),
    Output(component_id="pf-mc-lognorm-group", component_property="style"),
    Output(component_id="pf-mc-t-group", component_property="style"),
    Input(component_id="pf-monte-carlo-distribution", component_property="value"),
)
def show_hide_param_groups(distribution: str):
    """Show only the field group for the selected distribution."""
    hidden = {"display": "none"}
    return (
        None if distribution == "norm" else hidden,
        None if distribution == "lognorm" else hidden,
        None if distribution == "t" else hidden,
    )


@callback(
    Output(component_id="pf-mc-params-collapse", component_property="is_open"),
    Output(component_id="pf-mc-params-chevron", component_property="className"),
    Input(component_id="pf-mc-params-toggle", component_property="n_clicks"),
    State(component_id="pf-mc-params-collapse", component_property="is_open"),
    prevent_initial_call=True,
)
def toggle_mc_params_collapse(n_clicks, is_open):
    """Flip the distribution-parameters collapse and its chevron icon."""
    new_open = not is_open
    chevron = "bi bi-chevron-down me-2" if new_open else "bi bi-chevron-right me-2"
    return new_open, chevron


@callback(
    Output(component_id="pf-mc-t-df", component_property="invalid"),
    Input(component_id="pf-mc-t-df", component_property="value"),
    prevent_initial_call=True,
)
def validate_df(value):
    """Student's t requires df > 2 (okama validator)."""
    if value in (None, ""):
        return False
    return float(value) <= 2


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


@callback(
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
    # Rebalancing deviation
    State("pf-rebal-abs-deviation", "value"),
    State("pf-rebal-rel-deviation", "value"),
    # Cash flow strategy
    State("pf-initial-amount", "value"),
    State("pf-discount-rate", "value"),
    State("pf-ticker", "value"),
    State("pf-cf-strategy-type", "value"),
    State("pf-cf-frequency", "value"),
    State("pf-cf-amount", "value"),
    State("pf-cf-indexation", "value"),
    State("pf-cf-percentage", "value"),
    State("pf-cf-vds-percentage", "value"),
    State("pf-cf-vds-min-withdrawal", "value"),
    State("pf-cf-vds-max-withdrawal", "value"),
    State("pf-cf-vds-adjust-minmax", "value"),
    State("pf-cf-vds-floor", "value"),
    State("pf-cf-vds-ceiling", "value"),
    State("pf-cf-vds-adjust-fc", "value"),
    State("pf-cf-vds-indexation", "value"),
    State("pf-cf-cwd-amount", "value"),
    State({"type": "pf-cf-cwd-threshold", "index": ALL}, "value"),
    State({"type": "pf-cf-cwd-reduction", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-amount", "index": ALL}, "value"),
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
    # Rebalancing deviation
    abs_dev: Optional[float],
    rel_dev: Optional[float],
    # Cash flow strategy
    initial_amount: Optional[float],
    discount_rate: Optional[float],
    symbol: Optional[str],
    cf_strategy: str,
    cf_freq: str,
    cf_amount: Optional[float],
    cf_indexation: Optional[float],
    cf_pct: Optional[float],
    vds_pct: Optional[float],
    vds_min: Optional[float],
    vds_max: Optional[float],
    vds_adj_mm: bool,
    vds_floor: Optional[float],
    vds_ceil: Optional[float],
    vds_adj_fc: bool,
    vds_indexation: Optional[float],
    cwd_amount: Optional[float],
    cwd_thresholds: list,
    cwd_reductions: list,
    ts_dates: list,
    ts_amounts: list,
):
    cwd_tr = None
    if cwd_thresholds and cwd_reductions:
        pairs = [
            f"{t}:{r}" for t, r in zip(cwd_thresholds, cwd_reductions, strict=True) if t is not None and r is not None
        ]
        if pairs:
            cwd_tr = ",".join(pairs)

    cf_ts = None
    if ts_dates and ts_amounts:
        pairs = [f"{d}:{a}" for d, a in zip(ts_dates, ts_amounts, strict=True) if d and a is not None]
        if pairs:
            cf_ts = ",".join(pairs)

    # Scope cashflow params to active strategy only
    scoped_cf = scope_cashflow_params(
        cf_strategy=cf_strategy,
        cf_freq=cf_freq,
        cf_amount=cf_amount,
        cf_indexation=cf_indexation,
        cf_pct=cf_pct,
        vds_pct=vds_pct,
        vds_min=vds_min,
        vds_max=vds_max,
        vds_adj_mm=vds_adj_mm,
        vds_floor=vds_floor,
        vds_ceil=vds_ceil,
        vds_adj_fc=vds_adj_fc,
        vds_indexation=vds_indexation,
        cwd_amount=cwd_amount,
        cwd_tr=cwd_tr,
        cf_ts=cf_ts,
    )

    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        weights_list=weights_list,
        rebal=rebal,
        initial_amount=initial_amount,
        discount_rate=discount_rate,
        symbol=symbol,
        abs_dev=abs_dev,
        rel_dev=rel_dev,
        # scoped_cf carries cf_strategy too: None (omitted) when the selected
        # strategy has a zero primary flow value and no custom cash flows,
        # i.e. is effectively inactive.
        **scoped_cf,
    )


@callback(
    Output("pf-goto-ef", "href"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),  # weights
    Input("pf-base-currency", "value"),
    Input("pf-first-date", "value"),
    Input("pf-last-date", "value"),
    Input("pf-rebalancing-period", "value"),
    Input("pf-ticker", "value"),
)
def update_go_to_ef_link(
    tickers_list: Optional[list],
    weights_list: Optional[list],
    ccy: str,
    first_date: str,
    last_date: str,
    rebal: str,
    symbol: Optional[str],
) -> str:
    """Build the EF-page link carrying the portfolio.

    Standard frontier params (tickers/ccy/dates/rebal) define the frontier;
    the portfolio section is just weights + symbol. Same vocabulary as the
    EF "Backtest portfolio" link, in reverse.
    """
    tickers = [t for t in tickers_list if t]
    weights = [w for w in weights_list if w is not None]
    return create_link(
        href="/",
        tickers_list=tickers,
        ccy=ccy,
        first_date=first_date,
        last_date=last_date,
        rebal=rebal,
        weights_list=weights,
        symbol=symbol,
    )


@callback(
    Output({"type": "pf-dynamic-input", "index": MATCH}, "invalid"),
    Input({"type": "pf-dynamic-input", "index": MATCH}, "value"),
)
def validate_weight_input(value) -> bool:
    """Flag a portfolio weight as invalid when it is outside 0-100."""
    if value in (None, ""):
        return False
    return not 0 <= float(value) <= 100


# ----------------------- Ticker | Weight constructor -------------------------------------------
@callback(
    Output("dynamic-container", "children"),
    Input("pf_tickers_url", "data"),
    Input("pf_weights_url", "data"),
    Input("dynamic-add-filter", "n_clicks"),
    Input({"type": "pf-dynamic-remove", "index": ALL}, "n_clicks"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "id"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),
)
def update_rows_in_constructor(
    tickers, weights, n_clicks, remove_clicks, dropdown_ids, selected_tickers, selected_weights
):
    trigger = dash.ctx.triggered_id

    if trigger == "pf_tickers_url" or trigger == "pf_weights_url" or not dropdown_ids:
        rows = get_constructor_rows_from_url(tickers, weights)
    else:
        rows = get_current_constructor_rows(dropdown_ids, selected_tickers, selected_weights)
        if trigger == "dynamic-add-filter":
            next_index = max((row["index"] for row in rows), default=-1) + 1
            rows.append({"index": next_index, "symbol": None, "weight": None})
        elif isinstance(trigger, dict) and trigger.get("type") == "pf-dynamic-remove":
            rows = [row for row in rows if row["index"] != trigger["index"]]
            if not rows:
                next_index = max((row_id["index"] for row_id in dropdown_ids), default=-1) + 1
                rows = [{"index": next_index, "symbol": None, "weight": None}]

    return [
        append_row(row["index"], row["symbol"], row["weight"], get_weight_placeholder(rows, idx))
        for idx, row in enumerate(rows)
    ]


def get_constructor_rows_from_url(tickers, weights):
    tickers = tickers or []
    weights = weights or []
    row_count = max(len(tickers), len(weights), 1)
    return [
        {
            "index": index,
            "symbol": tickers[index] if index < len(tickers) else None,
            "weight": weights[index] if index < len(weights) else None,
        }
        for index in range(row_count)
    ]


def get_current_constructor_rows(dropdown_ids, selected_tickers, selected_weights):
    return [
        {
            "index": row_id["index"],
            "symbol": ticker,
            "weight": weight,
        }
        for row_id, ticker, weight in zip(dropdown_ids, selected_tickers, selected_weights, strict=True)
    ]


def get_weight_placeholder(rows, row_position):
    previous_weights_sum = sum(float(row["weight"]) for row in rows[:row_position] if row["weight"] is not None)
    remaining_weight = max(0, np.around(100 - previous_weights_sum, decimals=3))
    return f"0 - {remaining_weight:g}"


def append_row(row_index, symbol, weight, weight_placeholder):
    return dbc.Row(
        [
            dbc.Col(
                search_provider(
                    dmc.Select(
                        id={"type": "pf-dynamic-dropdown", "index": row_index},
                        data=get_selected_symbol_options([symbol] if symbol else None),
                        value=symbol,
                        placeholder="Type a ticker",
                        searchable=True,
                        clearable=True,
                        nothingFoundMessage="No matching tickers",
                        comboboxProps={"shadow": "md"},
                    )
                ),
                width=6,
            ),
            dbc.Col(
                dbc.Input(
                    id={"type": "pf-dynamic-input", "index": row_index},
                    placeholder=weight_placeholder,
                    value=weight,
                    type="number",
                    min=0,
                    max=100,
                ),
            ),
            # "auto" + ps-1 keeps the remove icon snug against the input
            # (same compact style as the CWD threshold rows)
            dbc.Col(
                dbc.Button(
                    html.I(className="bi bi-x-lg"),
                    id={"type": "pf-dynamic-remove", "index": row_index},
                    color="link",
                    class_name="p-0 text-secondary",
                    size="sm",
                    title="Remove asset",
                ),
                width="auto",
                class_name="ps-1 d-flex align-items-center",
            ),
        ],
    )


@callback(
    Output({"type": "pf-dynamic-dropdown", "index": MATCH}, "data"),
    Input({"type": "pf-dynamic-dropdown", "index": MATCH}, "searchValue"),
    Input({"type": "pf-dynamic-dropdown", "index": MATCH}, "value"),
)
def optimize_search_al(search_value, selected_value) -> list:
    if not search_value:
        raise PreventUpdate
    return search_symbol_options(search_value, [selected_value] if selected_value else None)


@callback(
    Output("pf-portfolio-weights-sum", "children"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
)
def print_weights_sum(values) -> str:
    # Single children Output: returning a (text, flag) tuple would serialize the
    # whole tuple into children and leak a bare bool — an invalid ReactNode.
    weights_sum = sum(float(x) for x in values if x)
    return f"Total: {np.around(weights_sum, decimals=3)}"


@callback(
    Output("pf-withdrawal-rate", "value"),
    Input("pf-initial-amount", "value"),
    Input("pf-cf-amount", "value"),
    Input("pf-cf-cwd-amount", "value"),
    Input("pf-cf-strategy-type", "value"),
    Input("pf-cf-frequency", "value"),
)
def print_withdrawal_rate(initial_amount, cf_amount, cwd_amount, strategy, frequency) -> str:
    freq_multiplier = {"month": 12, "quarter": 4, "half-year": 2, "year": 1}
    amount = cwd_amount if strategy == "cwd" else cf_amount
    if initial_amount and amount:
        periods_per_year = freq_multiplier.get(frequency, 12)
        withdrawal_rate = abs(float(amount)) * periods_per_year / float(initial_amount) * 100
    else:
        withdrawal_rate = 0
    return f"{withdrawal_rate:.0f}%"


@callback(
    Output("pf-submit-button", "disabled"),
    Output("pf-copy-link-button", "disabled"),
    Output("dynamic-add-filter", "disabled"),
    Output("pf-goto-menu", "disabled"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    Input("pf-rolling-window", "value"),
    Input("pf-monte-carlo-number", "valid"),
    Input("pf-monte-carlo-years", "valid"),
)
def disable_submit_add_link_buttons(
    tickers_list, weights_list, rolling_window_value, mc_number_valid, mc_years_valid
) -> Tuple[bool, bool, bool, bool]:
    """
    Disable "Add Asset", "Submit" and "Copy Link" buttons.

    disable "Add Asset" conditions:
    - weights and assets forms are not empty (don't have None)
    - number of tickers is more or equal than allowed (in settings)

    disable "Submit" conditions:
    - sum of weights is not 100
    - number of weights is not equal to the number of assets
    - rolling window size is natural number
    - MC number and MC forecast years are valid (incl. the number × years budget)

    disable "Copy Link" conditions:
    - "Submit"
    - number of tickers is more than allowed (in settings)

    disable "Go to" menu conditions (one gate for all three items):
    - "Copy Link"
    - number of unique tickers is < 2 (a frontier needs at least two assets)
    """
    add_condition1 = None in tickers_list or None in weights_list
    add_condition2 = len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS
    add_result = add_condition1 or add_condition2

    tickers_list = [i for i in tickers_list if i is not None]
    weights_list = [i for i in weights_list if i is not None]

    weights_sum = sum(float(x) for x in weights_list if x)
    weights_sum_is_not_100 = np.around(weights_sum, decimals=3) != 100.0
    # 150 + -50 sums to 100 but each weight must itself stay within 0-100
    weights_out_of_range = any(not 0 <= float(w) <= 100 for w in weights_list if w != "")

    weights_and_tickers_has_different_length = len(set(tickers_list)) != len(weights_list)
    rolling_not_natural = validators.validate_integer_bool(rolling_window_value)

    mc_number_is_incorrect = not mc_number_valid
    mc_years_is_incorrect = not mc_years_valid

    submit_result = (
        weights_sum_is_not_100
        or weights_out_of_range
        or weights_and_tickers_has_different_length
        or rolling_not_natural
        or mc_number_is_incorrect
        or mc_years_is_incorrect
    )

    link_condition = len(tickers_list) > settings.ALLOWED_NUMBER_OF_TICKERS
    link_result = submit_result or link_condition
    # EF needs at least two assets: a one-asset "frontier" is just a point.
    go_to_ef_result = bool(link_result or len(set(tickers_list)) < 2)
    return submit_result, link_result, add_result, go_to_ef_result


@callback(
    Output("pf-monte-carlo-number", "valid"),
    Output("pf-monte-carlo-number", "invalid"),
    Output("pf-monte-carlo-years", "valid"),
    Output("pf-monte-carlo-years", "invalid"),
    Input("pf-monte-carlo-number", "value"),
    Input("pf-monte-carlo-years", "value"),
)
def check_validity_monte_carlo(number, years):
    """
    Validate the Monte Carlo simulations number, forecast years and their combined budget.

    - number: integer in 0..MC_PORTFOLIO_MAX (0 means Monte Carlo is off)
    - years: integer in 1..MC_PORTFOLIO_YEARS_MAX
    - budget: number × years ≤ MC_PORTFOLIO_BUDGET (applied only when number > 0)

    Out-of-range typed values arrive from dcc as strings — they must be flagged
    invalid here (and gate Submit) instead of crashing the data callback.
    """
    number_ok = isinstance(number, int) and number in range(0, settings.MC_PORTFOLIO_MAX + 1)
    years_ok = isinstance(years, int) and years in range(1, settings.MC_PORTFOLIO_YEARS_MAX + 1)
    if number_ok and years_ok and number > 0 and number * years > settings.MC_PORTFOLIO_BUDGET:
        number_ok = years_ok = False
    number_marks = (number_ok, not number_ok) if number is not None else (False, False)
    years_marks = (years_ok, not years_ok) if years is not None else (False, False)
    return *number_marks, *years_marks


register_date_validation("pf-first-date")
register_date_validation("pf-last-date")

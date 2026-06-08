"""Find max withdrawal block (issue #22) — layout + callbacks.

The okama solver does not accept TimeSeriesStrategy, so the shared
``toggle_strategy_panels`` callback (``common.py``) hides ``pf-cf-find-block``
for the time_series strategy.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State

from common.html_elements.submit_spinner import create_submit_spinner
from .constants import FIND_GOAL_OPTIONS
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def _find_block():
    return html.Div(
        [
            html.Div(
                [
                    html.I(className="bi bi-chevron-right me-2", id="pf-cf-find-chevron"),
                    "Find max withdrawal",
                    html.I(className="bi bi-info-square ms-2", id="pf-cf-find-info-label"),
                    dbc.Tooltip(tl.pf_cf_find_block, target="pf-cf-find-info-label"),
                ],
                id="pf-cf-find-toggle",
                n_clicks=0,
                className="fw-bold",
                style={"cursor": "pointer", "userSelect": "none"},
            ),
            dbc.Collapse(
                html.Div(
                    [
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Goal",
                                            html.I(
                                                className="bi bi-info-square ms-2",
                                                id="pf-info-find-goal",
                                            ),
                                        ]
                                    ),
                                    dbc.Tooltip(tl.pf_cf_find_goal, target="pf-info-find-goal"),
                                    dcc.Dropdown(
                                        options=FIND_GOAL_OPTIONS,
                                        value="maintain_balance_pv",
                                        multi=False,
                                        clearable=False,
                                        searchable=False,
                                        id="pf-cf-find-goal",
                                    ),
                                ],
                                lg=12,
                                sm=12,
                            ),
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            [
                                                "Percentile",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-find-percentile",
                                                ),
                                            ],
                                            className="text-nowrap",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_cf_find_percentile,
                                            target="pf-info-find-percentile",
                                        ),
                                        dbc.Input(
                                            id="pf-cf-find-percentile",
                                            type="number",
                                            min=0,
                                            max=100,
                                            step=1,
                                            value=20,
                                        ),
                                        dbc.FormText("0 - 100"),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=6,
                                ),
                                dbc.Col(
                                    [
                                        html.Label(
                                            [
                                                "Target survival period",
                                                html.I(
                                                    className="bi bi-info-square ms-2",
                                                    id="pf-info-find-target-sp",
                                                ),
                                            ],
                                            className="text-nowrap",
                                        ),
                                        dbc.Tooltip(
                                            tl.pf_cf_find_target_sp,
                                            target="pf-info-find-target-sp",
                                        ),
                                        dbc.Input(
                                            id="pf-cf-find-target-sp",
                                            type="number",
                                            min=1,
                                            step=1,
                                            value=25,
                                        ),
                                        dbc.FormText("Years, below the forecast period"),
                                    ],
                                    lg=6,
                                    md=6,
                                    sm=6,
                                    id="pf-cf-find-target-sp-col",
                                    style={"display": "none"},
                                ),
                            ],
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Find",
                                                id="pf-cf-find-button",
                                                n_clicks=0,
                                                size="sm",
                                                color="secondary",
                                            ),
                                            html.Small(id="pf-cf-find-result", className="ms-2"),
                                        ],
                                        className="d-flex align-items-center",
                                    ),
                                    create_submit_spinner("pf-cf-find-spinner"),
                                    dbc.FormText(id="pf-cf-find-hint"),
                                ],
                            ),
                        ),
                    ],
                    className="vstack gap-2 p-2",
                ),
                id="pf-cf-find-collapse",
                is_open=False,
            ),
        ],
        id="pf-cf-find-block",
        className="mt-3",
    )


@callback(
    Output("pf-cf-find-collapse", "is_open"),
    Output("pf-cf-find-chevron", "className"),
    Input("pf-cf-find-toggle", "n_clicks"),
    State("pf-cf-find-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_find_collapse(n_clicks, is_open):
    """Flip the Find-max-withdrawal collapse and its chevron icon."""
    new_open = not is_open
    chevron = "bi bi-chevron-down me-2" if new_open else "bi bi-chevron-right me-2"
    return new_open, chevron


@callback(
    Output("pf-cf-find-target-sp-col", "style"),
    Input("pf-cf-find-goal", "value"),
)
def toggle_find_target_sp(goal):
    """Target survival period applies to the survival_period goal only."""
    return None if goal == "survival_period" else {"display": "none"}


@callback(
    Output("pf-cf-find-percentile", "invalid"),
    Output("pf-cf-find-target-sp", "invalid"),
    Input("pf-cf-find-percentile", "value"),
    Input("pf-cf-find-target-sp", "value"),
    Input("pf-monte-carlo-years", "value"),
)
def validate_find_inputs(percentile, target_sp, mc_years):
    """Validate the Find solver inputs.

    Out-of-range typed values arrive from dcc as strings (same behavior as the
    MC number/years inputs) — flag them invalid instead of crashing the solver
    callback.
    """
    percentile_ok = isinstance(percentile, int) and 0 <= percentile <= 100
    target_ok = isinstance(target_sp, int) and target_sp >= 1 and isinstance(mc_years, int) and target_sp < mc_years
    return not percentile_ok, not target_ok


@callback(
    Output("pf-cf-find-button", "disabled"),
    Output("pf-cf-find-hint", "children"),
    Input("pf-monte-carlo-number", "valid"),
    Input("pf-monte-carlo-years", "valid"),
    Input("pf-monte-carlo-number", "value"),
    Input("pf-initial-amount", "value"),
    Input("pf-cf-find-percentile", "invalid"),
    Input("pf-cf-find-target-sp", "invalid"),
    Input("pf-cf-find-goal", "value"),
)
def disable_find_button(
    mc_number_valid, mc_years_valid, mc_number, initial_amount, percentile_invalid, target_sp_invalid, goal
) -> tuple[bool, str]:
    """Gate the Find button on the same validity the solver needs.

    The hint explains the first failing condition; empty when enabled.
    """
    mc_on = isinstance(mc_number, int) and mc_number > 0
    if not mc_number_valid or not mc_years_valid or not mc_on:
        return True, "Requires Monte Carlo simulations > 0 and a valid forecast period."
    if initial_amount in (None, ""):
        return True, "Set the Initial amount."
    if percentile_invalid:
        return True, "Percentile must be an integer between 0 and 100."
    if goal == "survival_period" and target_sp_invalid:
        return True, "Target survival period must be an integer below the Monte Carlo forecast period."
    return False, ""


@callback(
    Output("pf-cf-find-result", "children", allow_duplicate=True),
    Output("pf-cf-find-result", "className", allow_duplicate=True),
    Input("pf-cf-strategy-type", "value"),
    prevent_initial_call=True,
)
def reset_find_result(_strategy) -> tuple[str, str]:
    """A found value targets one strategy's input — clear the stale result
    text when the user switches to a different strategy."""
    return "", "ms-2"

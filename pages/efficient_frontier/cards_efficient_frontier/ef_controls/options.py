"""Efficient Frontier options block (Plot type, MDP line, CML, Risk-free rate,
simulation mode with Monte Carlo / Grid inputs) and its callbacks: simulation
input visibility, grid-step options, risk-free enablement, the incompatible-
option sync and the Monte Carlo point-count validity."""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output

from common import settings as settings
from common.ef_grid import grid_step_options, AUTO_STEP
from .constants import PLOT_OPTIONS, TOGGLE_OPTIONS
import pages.efficient_frontier.cards_efficient_frontier.eng.ef_tooltips_options_txt as tl


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


def options_section(tickers):
    """The Options header and the Plot / MDP / CML / Risk-free / simulation rows.

    Returns a list of sibling rows so it can be splatted into the controls card
    without adding a wrapper element."""
    return [
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
                dbc.Col(lg=6, md=6, sm=12),
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
                        dbc.FormText("0 - 100 % (Format: XX.XX)"),
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
        dbc.Row(html.H6(children="Inside Efficient Frontier")),
        dbc.Row(
            [
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {"label": "Off", "value": "Off"},
                            {
                                "label": html.Span(
                                    [
                                        "Monte Carlo",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="info-sim-mc",
                                        ),
                                    ]
                                ),
                                "value": "Monte Carlo",
                            },
                            {
                                "label": html.Span(
                                    [
                                        "Grid",
                                        html.I(
                                            className="bi bi-info-square ms-2",
                                            id="info-sim-grid",
                                        ),
                                    ]
                                ),
                                "value": "Grid",
                            },
                        ],
                        value="Off",
                        id="ef-sim-mode",
                    ),
                    width=12,
                ),
                dbc.Tooltip(
                    tl.ef_options_simulation_mc,
                    target="info-sim-mc",
                ),
                dbc.Tooltip(
                    tl.ef_options_simulation_grid,
                    target="info-sim-grid",
                ),
            ],
            className="p-1",
        ),
        html.Div(
            dbc.Row(
                [
                    dbc.Label("Number of points", width=6),
                    dbc.Col(
                        [
                            dbc.Input(
                                type="number",
                                value=0,
                                id="monte-carlo-option",
                            ),
                            dbc.FormFeedback("", type="valid"),
                            dbc.FormFeedback(
                                f"it should be an integer number ≤{settings.MC_EF_MAX}",
                                type="invalid",
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="p-1",
            ),
            id="ef-mc-input-wrapper",
            style={"display": "none"},
        ),
        html.Div(
            dbc.Row(
                [
                    dbc.Label("Weight step", width=6),
                    dbc.Col(
                        dcc.Dropdown(
                            id="ef-grid-step",
                            options=grid_step_options(
                                len(tickers) if tickers else len(settings.default_symbols)
                            ),
                            value=AUTO_STEP,
                            clearable=False,
                        ),
                        width=6,
                    ),
                ],
                className="p-1",
            ),
            id="ef-grid-step-wrapper",
            style={"display": "none"},
        ),
    ]


@callback(
    Output("ef-mc-input-wrapper", "style"),
    Output("ef-grid-step-wrapper", "style"),
    Input("ef-sim-mode", "value"),
)
def toggle_simulation_inputs(mode: str) -> tuple[dict, dict]:
    """Show the Monte Carlo input or the grid step dropdown based on the mode."""
    hidden = {"display": "none"}
    shown: dict = {}
    if mode == "Monte Carlo":
        return shown, hidden
    if mode == "Grid":
        return hidden, shown
    return hidden, hidden


@callback(
    Output("ef-grid-step", "options"),
    Input("ef-symbols-list", "value"),
)
def update_grid_step_options(tickers_list) -> list[dict]:
    """Rebuild grid step options so steps over the point budget are disabled."""
    n_assets = len(tickers_list) if tickers_list else 0
    return grid_step_options(n_assets)


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
    Output("ef-sim-mode", "value"),
    Input("ef-plot-options", "value"),
    Input("mdp-line-option", "value"),
    Input("cml-option", "value"),
    Input("ef-sim-mode", "value"),
)
def sync_incompatible_options(plot_type, mdp_value, cml_value, sim_mode):
    plot_types = _normalize_plot_types(plot_type)
    mdp_value = mdp_value or "Off"
    cml_value = cml_value or "Off"
    sim_mode = sim_mode or "Off"
    triggered_id = dash.ctx.triggered_id

    sim_active = sim_mode in {"Monte Carlo", "Grid"}
    incompatible_selected = mdp_value == "On" or cml_value == "On" or sim_active
    pairwise_selected = "Pairwise" in plot_types

    if triggered_id in {"mdp-line-option", "cml-option", "ef-sim-mode"} and incompatible_selected:
        plot_types = [option for option in plot_types if option != "Pairwise"]
        pairwise_selected = False

    if triggered_id == "ef-plot-options" and pairwise_selected:
        mdp_value = "Off"
        cml_value = "Off"
        sim_mode = "Off"
        sim_active = False
        incompatible_selected = False

    if not plot_types:
        plot_types = ["Frontier"]

    pairwise_selected = "Pairwise" in plot_types
    mdp_cml_disabled = pairwise_selected

    if mdp_cml_disabled:
        mdp_value = "Off"
        cml_value = "Off"

    if pairwise_selected:
        sim_mode = "Off"
        sim_active = False

    pairwise_disabled = mdp_value == "On" or cml_value == "On" or sim_active

    return (
        _get_plot_options(pairwise_disabled=pairwise_disabled),
        plot_types,
        _get_toggle_options(disabled=mdp_cml_disabled),
        mdp_value,
        _get_toggle_options(disabled=mdp_cml_disabled),
        cml_value,
        sim_mode,
    )


@callback(
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

"""Display options section (Plot type / Include Inflation / Rolling Window) and
the callbacks that toggle the rolling-window input, the inflation switch and the
log-scale switch by the selected plot type."""

from typing import Tuple

import dash_bootstrap_components as dbc
from dash import html, callback
from dash.dependencies import Input, Output, State

import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def options_section():
    """The 'Options' header plus the Plot / Inflation / Rolling-window row.

    Returns a list of sibling rows so it can be splatted into the controls card
    without adding a wrapper element."""
    return [
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
    ]


@callback(
    Output(component_id="pf-rolling-window", component_property="disabled"),
    Input(component_id="pf-plot-option", component_property="value"),
)
def disable_rolling_input(plot_options: str) -> bool:
    return plot_options in {"wealth", "cumulative_return", "drawdowns", "distribution", "annual_return"}


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

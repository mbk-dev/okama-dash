"""Monte Carlo simulation section (simulations number, forecast period,
distribution type, distribution-parameters collapse, backtest) and its
callbacks: row visibility, distribution-group show/hide, the collapse toggle,
df validation and the number/years/budget validity."""

import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State

from common import settings as settings
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


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


def monte_carlo_section():
    """The Monte Carlo rows (header, number, period, distribution, parameters,
    backtest). Returns a list of sibling rows so it can be splatted into the
    controls card without adding a wrapper element."""
    return [
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

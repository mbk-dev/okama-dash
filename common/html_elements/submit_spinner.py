"""
Spinner shown under a page's Submit button while the main data callback runs.

The chart itself is wrapped in dcc.Loading, but on mobile the chart sits below
the fold (tables push it down), so that spinner is invisible when Submit is
pressed. Each page places this hidden spinner right under its Submit button and
toggles it via the main callback's `running` argument.
"""

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Output


def create_submit_spinner(spinner_id: str) -> html.Div:
    """Hidden spinner div; reveal it with `submit_spinner_running(spinner_id)`."""
    return html.Div(
        dbc.Spinner(color="primary"),
        id=spinner_id,
        style={"display": "none"},
        className="pt-2",
    )


def submit_spinner_running(spinner_id: str) -> list[tuple[Output, dict, dict]]:
    """`running=` spec for @callback: show the spinner while the callback runs."""
    return [(Output(spinner_id, "style"), {"display": "block"}, {"display": "none"})]

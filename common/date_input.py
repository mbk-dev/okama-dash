import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output


def current_month() -> str:
    """Current month as ``YYYY-MM``, evaluated at call time.

    Use this as the default for a 'Last Date' input instead of a module-level
    constant: a Gunicorn worker process is long-lived and a constant captured at
    import would freeze the default to the month the worker started in, silently
    truncating the freshest month of data once the calendar rolls over.
    """
    return pd.Timestamp.today().strftime("%Y-%m")

_CLIENTSIDE_JS = """
function(value) {
    if (!value) return [false, false, dash_clientside.no_update];
    var clean = value.replace(/[^0-9-]/g, '');
    if (clean !== value) value = clean;
    var valid = /^\\d{4}-\\d{2}$/.test(value);
    return [valid, !valid, value];
}
"""


def date_input(component_id, value=None, placeholder="2020-01"):
    return [
        dbc.Input(
            id=component_id,
            value=value,
            type="text",
            placeholder=placeholder,
        ),
        dbc.FormFeedback("Use YYYY-MM format", type="invalid"),
        dbc.FormText("Format: YYYY-MM"),
    ]


def register_date_validation(component_id):
    dash.clientside_callback(
        _CLIENTSIDE_JS,
        Output(component_id, "valid"),
        Output(component_id, "invalid"),
        Output(component_id, "value"),
        Input(component_id, "value"),
    )

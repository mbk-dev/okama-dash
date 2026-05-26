import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

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

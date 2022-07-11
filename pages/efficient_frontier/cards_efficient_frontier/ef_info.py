import dash_bootstrap_components as dbc
from dash import html

card_ef_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="ef-info"),
            html.H5("Assets names"),
            html.Div(id="ef-assets-names"),
        ]
    ),
    class_name="mb-3",
)

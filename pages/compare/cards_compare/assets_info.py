import dash_bootstrap_components as dbc
from dash import html

card_assets_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="al-compare-info"),
            html.H5(children="Assets names"),
            html.Div(id="al-assets-names"),
        ]
    ),
    class_name="mb-3",
)

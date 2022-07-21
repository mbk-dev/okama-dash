import dash_bootstrap_components as dbc
from dash import html

card_table = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Statistics table"),
                    html.Div(id="al-describe-table"),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

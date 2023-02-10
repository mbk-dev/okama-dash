from dash import html
import dash_bootstrap_components as dbc
from dash import dcc

card_transition_map = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dcc.Loading(dcc.Graph(id="ef-transition-map-graf"))
                ],
                id="ef-transition-map-graf-div"
            )
        ]
    ),
    class_name="mb-3",
)
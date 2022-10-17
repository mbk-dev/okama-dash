import dash_bootstrap_components as dbc
from dash import dcc

card_graf = dbc.Card(
    dbc.CardBody(
        [
            dcc.Loading(dcc.Graph(id="ef-graf")),
        ]
    ),
    class_name="mb-3",
)

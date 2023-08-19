from dash import html
import dash_bootstrap_components as dbc
from dash import dcc

card_graf = dbc.Card(
    dbc.CardBody([html.Div(dcc.Loading(dcc.Graph(id="ef-graf")))]),
    class_name="mb-3",
)

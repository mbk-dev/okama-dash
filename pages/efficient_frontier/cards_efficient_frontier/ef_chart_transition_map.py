from dash import html, dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

card_transition_map = dbc.Card(
    dbc.CardBody([html.Div([dcc.Loading(dcc.Graph(id="ef-transition-map-graf"))], id="ef-transition-map-graf-div")]),
    class_name="mb-3",
)

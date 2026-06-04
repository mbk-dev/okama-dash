from dash import html, dcc
import dash_bootstrap_components as dbc

card_transition_map = dbc.Card(
    dbc.CardBody([html.Div([dcc.Loading(dcc.Graph(id="ef-transition-map-graf"))], id="ef-transition-map-graf-div")]),
    class_name="mb-3",
)

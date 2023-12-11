from dash import html, dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

card_transition_map = dbc.Card(
    dbc.CardBody([html.Div(
        [dcc.Loading(dcc.Graph(id="ef-transition-map-graf"))],
        id="ef-transition-map-graf-div")]),
    class_name="mb-3",
)

# @callback(Output("ef-transition-map-graf-div", "hidden"), Input("ef-submit-button", "n_clicks"))
# def hide_ef_graf(n_clicks):
#     return n_clicks == 0

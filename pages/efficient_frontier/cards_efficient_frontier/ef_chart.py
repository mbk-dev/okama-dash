from dash import html, dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

card_graf = dbc.Card(
    dbc.CardBody([html.Div(
        [dcc.Loading(dcc.Graph(id="ef-graf"))],
        id="ef-graf-div"
    )]),
    class_name="mb-3",
)


@callback(Output("ef-graf-div", "hidden"), Input("ef-submit-button-state", "n_clicks"))
def hide_ef_graf(n_clicks):
    return n_clicks == 0

import dash_bootstrap_components as dbc
from dash import dcc, callback, html, Input, Output

card_graf_benchmark = dbc.Card(
    dbc.CardBody(
        html.Div(
            [
                dcc.Loading(dcc.Graph(id="benchmark-graph"))
            ],
            id="benchmark_graf_div"
        ),
        class_name="mb-3",
    )
)


@callback(Output("benchmark_graf_div", "hidden"), Input("benchmark-submit-button", "n_clicks"))
def hide_bch_graf(n_clicks):
    return n_clicks == 0

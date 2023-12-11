import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html, callback
from dash.dependencies import Input, Output

card_graf_compare = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dcc.Loading(
                        [
                            dcc.Graph(id="al-wealth-indexes"),
                            html.Div(
                                daq.BooleanSwitch(
                                    id="logarithmic-scale-switch",
                                    on=False,
                                    label="Logarithmic Y-Scale",
                                    labelPosition="bottom",
                                ),
                                id="al-logarithmic-scale-switch-div",
                            ),
                        ],
                    )
                ],
                id="al-graf-div",
            )
        ]
    ),
    class_name="mb-3",
)


@callback(Output("al-graf-div", "hidden"), Input("al-submit-button", "n_clicks"))
def hide_al_graf(n_clicks):
    return n_clicks == 0

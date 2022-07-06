import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import html, dcc

card_graf = dbc.Card(
    dbc.CardBody(
        [
            dcc.Loading(
                [
                    dcc.Graph(id="wealth-indexes"),
                    daq.BooleanSwitch(
                        id="logarithmic-scale-switch",
                        on=False,
                        label="Logarithmic Y-Scale",
                        labelPosition="bottom",
                    ),
                ],
            )
        ]
    ),
    class_name="mb-3",
)

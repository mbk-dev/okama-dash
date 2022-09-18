import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc

card_graf_portfolio = dbc.Card(
    dbc.CardBody(
        [
            dcc.Loading(
                [
                    dcc.Graph(id="pf-wealth-indexes"),
                    daq.BooleanSwitch(
                        id="pf-logarithmic-scale-switch",
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

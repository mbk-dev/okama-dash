import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html

card_graf_compare = dbc.Card(
    dbc.CardBody(
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
                        id="al-logarithmic-scale-switch-div"
                    )
                ],
            )
        ]
    ),
    class_name="mb-3",
)

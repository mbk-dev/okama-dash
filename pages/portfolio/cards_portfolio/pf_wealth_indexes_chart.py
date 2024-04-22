import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html

card_graf_portfolio = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dcc.Loading(
                        [
                            dcc.Graph(id="pf-wealth-indexes"),
                            html.Div(
                                daq.BooleanSwitch(
                                    id="pf-logarithmic-scale-switch",
                                    on=False,
                                    label="Logarithmic Y-Scale",
                                    labelPosition="bottom",
                                ),
                                id="pf-logarithmic-scale-switch-div",
                            ),
                        ],
                    )
                ],
                id="portfolio_graf_div",
            )
        ]
    ),
    class_name="mb-3",
)


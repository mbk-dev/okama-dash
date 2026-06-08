"""Chart card for macro pages: full-bleed on mobile, download-data link below."""

import dash_bootstrap_components as dbc
from dash import dcc, html


def macro_chart_card(page_prefix: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            dcc.Loading(
                [
                    dcc.Graph(id=f"{page_prefix}-chart"),
                    html.Div(
                        [
                            dbc.Button(
                                "Download data",
                                id=f"{page_prefix}-download-data-button",
                                color="link",
                                outline=False,
                                external_link=False,
                            ),
                            dcc.Store(id=f"{page_prefix}-store-chart-data", storage_type="session"),
                            dcc.Download(id=f"{page_prefix}-download-xlsx"),
                        ],
                        style={"textAlign": "right"},
                    ),
                ]
            )
        ),
        class_name="chart-card mb-3",
    )

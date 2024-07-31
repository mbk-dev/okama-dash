import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State

from common.xlsx import json_to_download_xlsx_object

card_graf_compare = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dcc.Loading(
                        [
                            dcc.Graph(id="al-wealth-indexes"),
                            html.Div(
                                dbc.Row(
                                    [
                                        dbc.Col(lg=2, md=2, sm=0,),
                                        dbc.Col(
                                            html.Div(
                                                daq.BooleanSwitch(
                                                    id="logarithmic-scale-switch",
                                                    on=False,
                                                    label="Logarithmic Y-Scale",
                                                    labelPosition="bottom",
                                                ),
                                            id="al-logarithmic-scale-switch-div",
                                            )
                                        ),
                                        dbc.Col(
                                            # download data button
                                            [html.Div(
                                                [
                                                    dbc.Button(
                                                        "Download data",
                                                        id="al-download-data-button",
                                                        className="position-relative",
                                                        color="link",
                                                        outline=False,
                                                        external_link=False,
                                                    ),
                                                    dcc.Store(id="al-store-chart-data", storage_type='session'),
                                                    dcc.Download(id="al-download-dataframe-xlsx"),
                                                ],
                                                style={"text-align": "center"},
                                            )],
                                            lg=2, md=2, sm=12,
                                        )
                                    ]
                                )
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


@callback(
    Output("al-download-dataframe-xlsx", "data"),
    Input("al-download-data-button", "n_clicks"),
    State("al-store-chart-data", "data"),
    prevent_initial_call=True,
)
def pf_download_excel(n_clicks, json_data):
    return json_to_download_xlsx_object(json_data)

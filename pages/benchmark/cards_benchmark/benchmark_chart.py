import dash_bootstrap_components as dbc
from dash import dcc, callback, html, Input, Output, State

from common.xlsx import json_to_download_xlsx_object

card_graf_benchmark = dbc.Card(
    dbc.CardBody(
        html.Div(
            [
                dcc.Loading(
                    [
                        dcc.Graph(id="benchmark-graph"),
                        html.Div(
                            [
                                dbc.Button(
                                    "Download data",
                                    id="benchmark-download-data-button",
                                    className="position-relative",
                                    color="link",
                                    outline=False,
                                    external_link=False,
                                ),
                                dcc.Store(id="benchmark-store-chart-data", storage_type='session'),
                                dcc.Download(id="benchmark-download-dataframe-xlsx"),
                            ],
                            style={"text-align": "right"},
                        )
                    ]
                )
            ], id="benchmark_graf_div"),
        class_name="mb-3",
    )
)


@callback(
    Output("benchmark-download-dataframe-xlsx", "data"),
    Input("benchmark-download-data-button", "n_clicks"),
    State("benchmark-store-chart-data", "data"),
    prevent_initial_call=True,
)
def pf_download_excel(n_clicks, json_data):
    return json_to_download_xlsx_object(json_data)

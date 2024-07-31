import dash.exceptions
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_daq as daq

import pandas as pd

card_graf_portfolio = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dcc.Loading(
                        [
                            dcc.Graph(id="pf-wealth-indexes"),
                            html.Div(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            # logarithmic scale button
                                            html.Div(
                                                daq.BooleanSwitch(
                                                    id="pf-logarithmic-scale-switch",
                                                    on=False,
                                                    label="Logarithmic Y-Scale",
                                                    labelPosition="bottom",
                                                ),
                                                style={"text-align": "right"},
                                                id="pf-logarithmic-scale-switch-div",
                                            ),
                                        ),
                                        dbc.Col(
                                            # download data button
                                            [html.Div(
                                                [
                                                    dbc.Button(
                                                        "Download data",
                                                        id="pf-download-data-button",
                                                        className="position-relative",
                                                        color="link",
                                                        outline=False,
                                                        external_link=False,
                                                    ),
                                                    dcc.Store(id="pf-store-chart-data", storage_type='session'),
                                                    dcc.Download(id="pf-download-dataframe-xlsx"),
                                                ],
                                                style={"text-align": "right"},
                                            )],
                                            lg=2, md=2, sm=6,
                                        )
                                    ]
                                ),

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


@callback(
    Output("pf-download-dataframe-xlsx", "data"),
    Input("pf-download-data-button", "n_clicks"),
    State("pf-store-chart-data", "data"),
    prevent_initial_call=True,
)
def pf_download_excel(n_clicks, json_data):
    if not json_data:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(json_data, convert_axes=False, orient="split")
    return dcc.send_data_frame(df.to_excel, "okama.xlsx", sheet_name="okama_data")



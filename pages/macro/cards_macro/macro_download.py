"""Per-chart "Download data" wiring shared by macro pages (benchmark pattern).

The main callback writes the chart's dataframe as JSON into a dcc.Store; the
download button converts that JSON to an xlsx file. Each page registers its own
callback via register_macro_download(prefix).
"""

import dash
from dash import Input, Output, State, callback

from common.xlsx import json_to_download_xlsx_object


def download_from_store(n_clicks, json_data):
    if not n_clicks or not json_data:
        raise dash.exceptions.PreventUpdate
    return json_to_download_xlsx_object(json_data)


def register_macro_download(prefix: str) -> None:
    callback(
        Output(f"{prefix}-download-xlsx", "data"),
        Input(f"{prefix}-download-data-button", "n_clicks"),
        State(f"{prefix}-store-chart-data", "data"),
        prevent_initial_call=True,
    )(download_from_store)

from typing import Tuple

import dash_bootstrap_components as dbc
from dash import html, callback, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info

card_benchmark_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="benchmark-info", children="Start to select assets to see the information"),
            html.H5("Assets names"),
            html.Div(id="benchmark-assets-names", children="Start to select assets to see the information"),
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("benchmark-assets-names", "children"),
    Output("benchmark-info", "children"),
    Input("benchmark-assets-list", "value"),  # assets tickers
    Input("select-benchmark", "value"),  # benchmark ticker
    Input("benchmark-base-currency", "value"),  # currency
    prevent_initial_call=False,
)
def pf_update_asset_names_info(
    assets: list, benchmark: str, ccy: str
) -> Tuple[dash_table.DataTable, dash_table.DataTable]:
    assets_to_compare = [i for i in assets if i is not None]
    assets = [benchmark] + assets_to_compare if benchmark else assets_to_compare
    if not assets:
        raise PreventUpdate
    al_object = ok.AssetList(assets, ccy=ccy, inflation=False)
    names_table = get_assets_names(al_object)
    info_table = get_info(al_object)
    return names_table, info_table

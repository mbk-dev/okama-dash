import dash_bootstrap_components as dbc
from dash import html, callback, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info

card_ef_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="ef-info", children="Start to select assets to see the information"),
            html.H5("Assets names"),
            html.Div(id="ef-assets-names", children="Start to select assets to see the information"),
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("ef-assets-names", "children"),
    Output("ef-info", "children"),
    Input("ef-symbols-list", "value"),  # tickers
    prevent_initial_call=False,
)
def pf_update_asset_names_info(assets: list) -> tuple[dash_table.DataTable, dash_table.DataTable]:
    assets = [i for i in assets if i is not None]
    if not assets:
        raise PreventUpdate
    al_object = ok.AssetList(assets)
    names_table = get_assets_names(al_object)
    info_table = get_info(al_object)
    return names_table, info_table

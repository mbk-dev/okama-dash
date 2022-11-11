import dash_bootstrap_components as dbc
from dash import html, callback, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info

card_assets_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="al-compare-info"),
            html.H5(children="Assets names"),
            html.Div(id="al-assets-names"),
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("al-assets-names", "children"),
    Output("al-compare-info", "children"),
    Input("al-symbols-list", "value"),  # tickers
    Input("al-base-currency", "value"),  # currency
    Input("al-inflation-switch", "value"),  # inflation
    prevent_initial_call=False,
)
def pf_update_asset_names_info(assets: list, ccy: str, inflation: bool) -> dash_table.DataTable:
    assets = [i for i in assets if i is not None]
    if not assets:
        raise PreventUpdate
    al_object = ok.AssetList(assets, ccy=ccy, inflation=inflation)
    names_table = get_assets_names(al_object)
    info_table = get_info(al_object)
    return names_table, info_table

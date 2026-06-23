import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import html, callback
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

import okama as ok

from common.html_elements.info_ag_grid import names_and_info_tables

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
def pf_update_asset_names_info(assets: list) -> tuple[dag.AgGrid, dag.AgGrid]:
    assets = [i for i in assets if i is not None]
    if not assets:
        raise PreventUpdate
    # inflation=False matches the frontier (also built inflation=False) and the
    # benchmark page's info panel. With okama's default inflation=True the
    # default-currency inflation series (e.g. USD.INFL), published ~1 month late,
    # would cap "Last available date" a month behind the actual asset data.
    return names_and_info_tables(lambda: ok.AssetList(assets, inflation=False))

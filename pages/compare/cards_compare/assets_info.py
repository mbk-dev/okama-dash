import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import html, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import okama as ok

from common.html_elements.info_ag_grid import names_and_info_tables
from common.url_portfolio import split_portfolio_from_selection

card_assets_info = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Information"),
            html.Div(id="al-compare-info", children="Start to select assets to see the information"),
            html.H5(children="Assets names"),
            html.Div(id="al-assets-names", children="Start to select assets to see the information"),
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
    State("al-url-portfolio", "data"),
    prevent_initial_call=True,
)
def pf_update_asset_names_info(
    assets: list, ccy: str, inflation: bool, pf_def: dict | None
) -> tuple[dag.AgGrid, dag.AgGrid]:
    if not assets:
        raise PreventUpdate
    assets = [i for i in assets if i is not None]
    # The portfolio chip is not a DB symbol: the info panel shows DB assets only.
    assets, _ = split_portfolio_from_selection(assets, pf_def)
    if not assets:
        raise PreventUpdate
    return names_and_info_tables(lambda: ok.AssetList(assets, ccy=ccy, inflation=inflation))

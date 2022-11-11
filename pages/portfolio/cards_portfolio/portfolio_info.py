import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import html, dcc, callback, ALL, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from dash.exceptions import PreventUpdate
import okama as ok

from common.html_elements.info_dash_table import get_assets_names, get_info
from common.mobile_screens import adopt_small_screens

card_assets_info = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H5("Asset Allocation"),
                            dcc.Graph(id="pf-asset-allocation", style={"height": 200, "width": "100%"}),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.H5("Information"),
                            html.Div(id="pf-asset-list-info", children="Start to select assets to see the information"),
                        ]
                    ),
                ]
            ),
            html.H5(children="Assets names"),
            html.Div(id="pf-assets-names", children="Start to select assets to see the information"),
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("pf-asset-allocation", "figure"),
    Output("pf-asset-allocation", "config"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    # user screen info
    Input(component_id="store", component_property="data"),
)
def generate_pie_chart(tickers, weights, screen):
    weights_sum = sum(float(x) for x in weights if x)
    if np.around(weights_sum, decimals=3) < 100:
        not_allocated_weight = 100 - weights_sum if 100 - weights_sum > 0 else 0
        weights.append(not_allocated_weight)
        tickers.append("Not Allocated")
    elif np.around(weights_sum, decimals=3) > 100:
        raise PreventUpdate

    df = pd.DataFrame({"Assets": tickers, "Weights": weights})
    fig = px.pie(df, values="Weights", names="Assets", hole=0)
    # Change layout for screen sizes
    fig, config = adopt_small_screens(fig, screen)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
    )
    return fig, config


@callback(
    Output("pf-assets-names", "children"),
    Output("pf-asset-list-info", "children"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),  # tickers
    Input("pf-base-currency", "value"),  # currency
    Input("pf-inflation-switch", "value"),  # inflation
    prevent_initial_call=True,
)
def pf_update_asset_names_info(assets: list, ccy: str, inflation: bool) -> dash_table.DataTable:
    assets = [i for i in assets if i is not None]
    if not assets:
        raise PreventUpdate
    al_object = ok.AssetList(assets, ccy=ccy, inflation=inflation)
    names_table = get_assets_names(al_object)
    info_table = get_info(al_object)
    return names_table, info_table

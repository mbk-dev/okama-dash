from collections.abc import Callable

import dash_ag_grid as dag
import okama
import pandas as pd
import requests
from dash import html

INFO_UNAVAILABLE_TEXT = "Information is unavailable for the selected symbols."


def names_and_info_tables(al_factory: Callable[[], okama.AssetList]) -> tuple:
    """Build the (names, info) panel tables, degrading gracefully.

    Tickers arriving from shareable links can be unknown to okama (delisted
    symbols, a ticker without a namespace) — ok.AssetList then raises an
    HTTPError 404 or a ValueError. Show a short message instead of a 500.
    """
    try:
        al_object = al_factory()
        return get_assets_names(al_object), get_info(al_object)
    except (ValueError, requests.exceptions.HTTPError):
        return (
            html.P(INFO_UNAVAILABLE_TEXT, className="text-muted"),
            html.P(INFO_UNAVAILABLE_TEXT, className="text-muted"),
        )


def get_assets_names(al_object: okama.AssetList) -> dag.AgGrid:
    """
    Render AgGrid table with assets names.
    """
    names_df = (
        pd.DataFrame.from_dict(al_object.names, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "Ticker", 0: "Name"})[["Ticker", "Name"]]
    )
    return dag.AgGrid(
        rowData=names_df.to_dict(orient="records"),
        columnDefs=[
            {"field": "Ticker", "wrapText": True, "autoHeight": True},
            {"field": "Name", "wrapText": True, "autoHeight": True},
        ],
        defaultColDef={"resizable": False, "sortable": False},
        columnSize="responsiveSizeToFit",
        dashGridOptions={"domLayout": "autoHeight"},
        style={"height": None},
    )


def get_info(al_object) -> dag.AgGrid:
    """
    Render AgGrid table with information about assets available historical period: length, first date, last date etc.
    """
    newest_asset_date = al_object.assets_first_dates[al_object.newest_asset].strftime("%Y-%m")
    ccy = al_object.currency
    al_object.assets_first_dates.pop(ccy)
    eldest_ticker = list(al_object.assets_first_dates)[0]
    eldest_asset_date = al_object.assets_first_dates[eldest_ticker].strftime("%Y-%m")
    info_list = [
        {"Property": "First available date", "Value": al_object.first_date.strftime("%Y-%m")},
        {"Property": "Last available date", "Value": al_object.last_date.strftime("%Y-%m")},
        {"Property": "Available period length", "Value": al_object._pl_txt},
        {
            "Property": "Shortest available history",
            "Value": f"{al_object.newest_asset} - {newest_asset_date}",
        },
        {
            "Property": "Longest available history",
            "Value": f"{eldest_ticker} - {eldest_asset_date}",
        },
    ]
    if len(al_object.symbols) < 2:
        # no need in "Shortest history" and "Longest history" if only one ticker
        info_list = info_list[:3]
    return dag.AgGrid(
        rowData=info_list,
        columnDefs=[
            {"field": "Property", "wrapText": True, "autoHeight": True},
            {"field": "Value", "wrapText": True, "autoHeight": True},
        ],
        defaultColDef={"resizable": False, "sortable": False},
        columnSize="responsiveSizeToFit",
        dashGridOptions={"domLayout": "autoHeight"},
        style={"height": None},
    )

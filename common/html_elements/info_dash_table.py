import okama
import pandas as pd
from dash import dash_table


def get_assets_names(al_object: okama.AssetList) -> dash_table.DataTable:
    """
    Render DataTable with assets names.
    """
    names_df = (
        pd.DataFrame.from_dict(al_object.names, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "Ticker", 0: "Name"})[["Ticker", "Name"]]
    )
    return dash_table.DataTable(
        data=names_df.to_dict(orient="records"),
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },
        # page_size=4,
    )


def get_info(al_object) -> dash_table.DataTable:
    """
    Render DataTable with information about assets available historical period: length, first date, last date etc.
    """
    newest_asset_date = al_object.assets_first_dates[al_object.newest_asset].strftime("%Y-%m")
    ccy = al_object.currency
    al_object.assets_first_dates.pop(ccy)
    eldest_ticker = list(al_object.assets_first_dates)[0]
    eldest_asset_date = al_object.assets_first_dates[eldest_ticker].strftime("%Y-%m")
    info_list = [
        {"Property": "First Date", "Value": al_object.first_date.strftime("%Y-%m")},
        {"Property": "Last Date", "Value": al_object.last_date.strftime("%Y-%m")},
        {"Property": "Period length", "Value": al_object._pl_txt},
        {
            "Property": "Shortest history",
            "Value": f"{al_object.newest_asset} - {newest_asset_date}",
        },
        {
            "Property": "Longest history",
            "Value": f"{eldest_ticker} - {eldest_asset_date}",
        },
    ]
    if len(al_object.symbols) < 2:
        # no need in "Shortest history" and "Longest history" if only one ticker
        info_list = info_list[:3]
    return dash_table.DataTable(
        data=info_list,
        style_data={"whiteSpace": "normal", "height": "auto"},
    )

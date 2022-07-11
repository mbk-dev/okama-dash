import okama
import pandas as pd
from dash import dash_table


def get_assets_names(al_object: okama.AssetList) -> dash_table.DataTable:
    names_df = (
        pd.DataFrame.from_dict(al_object.names, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "Ticker", 0: "Name"})[["Ticker", "Name"]]
    )
    return dash_table.DataTable(
        data=names_df.to_dict(orient="records"),
        style_data={"whiteSpace": "normal", "height": "auto",},
        page_size=4,)


def get_info(al_object):
    newest_asset_date = al_object.assets_first_dates[al_object.newest_asset].strftime("%Y-%m")
    eldest_asset_date = al_object.assets_first_dates[al_object.eldest_asset].strftime("%Y-%m")
    info_dict = [
        {"Property": "First Date", "Value": al_object.first_date.strftime("%Y-%m")},
        {"Property": "Last datee", "Value": al_object.last_date.strftime("%Y-%m")},
        {"Property": "Period length", "Value": al_object._pl_txt},
        {"Property": "Asset with shortest history", "Value": f"{al_object.newest_asset} - {newest_asset_date}"},
        {"Property": "Asset with longest history", "Value": f"{al_object.eldest_asset} - {eldest_asset_date}"}
    ]
    info_table = dash_table.DataTable(
        data=info_dict,
        style_data={"whiteSpace": "normal", "height": "auto"},
    )
    return info_table

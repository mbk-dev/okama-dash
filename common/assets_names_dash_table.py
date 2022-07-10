import okama
import pandas as pd
from dash import dash_table


def get_assets_names(al_object: okama.AssetList):
    names_df = (
        pd.DataFrame.from_dict(al_object.names, orient="index")
        .reset_index(drop=False)
        .rename(columns={"index": "Ticker", 0: "Long name"})[["Ticker", "Long name"]]
    )
    names_table = dash_table.DataTable(
        data=names_df.to_dict(orient="records"),
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },
        page_size=4,
    )
    return names_table

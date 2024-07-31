import dash.exceptions
import pandas as pd
from dash import dcc


def json_to_download_xlsx_object(json_data):
    """
    Convert stored json format data (from chart) to object for dcc.Download.
    """
    if not json_data:
        raise dash.exceptions.PreventUpdate
    df = pd.read_json(json_data, convert_axes=False, orient="split")
    download_excel_object = dcc.send_data_frame(df.to_excel, "okama.xlsx", sheet_name="okama_data")
    return download_excel_object


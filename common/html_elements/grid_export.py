"""
Xlsx export helper for dash-ag-grid components.

Provides a reusable export button and conversion function for server-side xlsx export.
"""

import dash.exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc


def create_xlsx_export_button(button_id: str) -> dbc.Button:
    """
    Create an xlsx export button styled per AGENTS.md conventions (inline action).

    Args:
        button_id: Unique ID for the button element.

    Returns:
        dbc.Button configured for xlsx export trigger.
    """
    return dbc.Button(
        "Export xlsx",
        id=button_id,
        color="secondary",
        outline=True,
        size="sm",
    )


def rowdata_to_xlsx_download(
    row_data: list[dict] | None,
    filename: str,
    sheet_name: str = "okama_data",
):
    """
    Convert AG Grid rowData to xlsx download object for dcc.Download.

    Args:
        row_data: List of dicts from AG Grid's rowData prop.
        filename: Output filename (must end with .xlsx).
        sheet_name: Excel sheet name.

    Returns:
        dcc.send_data_frame result for dcc.Download.

    Raises:
        dash.exceptions.PreventUpdate: If row_data is empty or None.
    """
    if not row_data:
        raise dash.exceptions.PreventUpdate

    df = pd.DataFrame(row_data)
    return dcc.send_data_frame(df.to_excel, filename, sheet_name=sheet_name, index=False)

"""
Xlsx export helper for dash-ag-grid components.

Provides a reusable export button and conversion function for server-side xlsx export.
"""

import dash.exceptions
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc

# Excel number formats mirroring the on-page AG Grid value formatters
# (assets/dashAgGridFunctions.js). The exported file shows the same
# percent/decimal/integer rendering as the grid, while cells keep raw
# numeric values so Excel formulas still work.
_EXCEL_NUMBER_FORMATS = {
    "percent": "0.00%",  # formatPercentGuarded: 0.0834 -> 8.34%
    "decimal": "0.00",  # formatDecimalGuarded: 19.0999 -> 19.10
    "int": "#,##0",  # formatGroupedIntGuarded: 13456.78 -> 13,457
}


def percent_column_formats(
    row_data: list[dict] | None,
    exclude: tuple[str, ...] = ("property", "period"),
) -> dict[str, str] | None:
    """
    Build the column_formats mapping for a describe-statistics grid.

    Every column except the label columns (property, period) holds percent
    values in okama describe() tables.

    Args:
        row_data: List of dicts from AG Grid's rowData prop.
        exclude: Label columns to leave unformatted.

    Returns:
        Mapping of column field -> "percent", or None when row_data is empty.
    """
    if not row_data:
        return None
    return {col: "percent" for col in row_data[0] if col not in exclude}


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
    n_clicks: int | None,
    row_data: list[dict] | None,
    filename: str,
    sheet_name: str = "okama_data",
    column_formats: dict[str, str] | None = None,
):
    """
    Convert AG Grid rowData to xlsx download object for dcc.Download.

    Args:
        n_clicks: Export button n_clicks. Guarded because Dash fires the
            callback when a dynamically created button first renders
            (prevent_initial_call does not apply to components inserted
            after page load), and that must not trigger a download.
        row_data: List of dicts from AG Grid's rowData prop.
        filename: Output filename (must end with .xlsx).
        sheet_name: Excel sheet name.
        column_formats: Optional mapping of column field -> format kind
            ("percent", "decimal" or "int"). Mapped columns get the matching
            Excel number format so the file shows what the grid shows;
            unmapped columns keep the General format.

    Returns:
        dcc.send_bytes result for dcc.Download.

    Raises:
        dash.exceptions.PreventUpdate: If the button was never clicked,
            or row_data is empty or None.
    """
    if not n_clicks or not row_data:
        raise dash.exceptions.PreventUpdate

    df = pd.DataFrame(row_data)

    def write_xlsx(buffer):
        # Explicit xlsxwriter engine: the column-format API below is
        # xlsxwriter-specific (pandas may default to openpyxl when installed).
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                kind = (column_formats or {}).get(col)
                if kind:
                    cell_format = writer.book.add_format({"num_format": _EXCEL_NUMBER_FORMATS[kind]})
                    worksheet.set_column(idx, idx, None, cell_format)

    return dcc.send_bytes(write_xlsx, filename)

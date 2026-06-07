"""describe() -> dash-ag-grid builders shared by all macro pages."""

import dash_ag_grid as dag
import pandas as pd

# Formatter functions live in assets/dashAgGridFunctions.js — inline
# typeof-guards are silently rejected by the dash-ag-grid function-string
# parser (same constraint as the Compare statistics grid).
_FORMATTERS = {
    "percent": "formatPercentGuarded(params.value)",
    "decimal": "formatDecimalGuarded(params.value)",
}


def build_describe_table(describes: list[pd.DataFrame]) -> pd.DataFrame:
    """Outer-merge single-symbol describe() frames on (property, period).

    Shared periods (YTD/1/5/10 years) align into one row; full-period rows with
    symbol-specific period strings stay as separate rows with NaN gaps, which
    the grid renders as blank cells.
    """
    merged = describes[0]
    for df in describes[1:]:
        merged = merged.merge(df, on=["property", "period"], how="outer", sort=False)
    return merged


def build_stats_grid(stats_df: pd.DataFrame, grid_id: str, value_format: str = "percent") -> dag.AgGrid:
    """Informational AG Grid for a merged describe() table."""
    formatter = _FORMATTERS[value_format]
    column_defs: list[dict] = []
    for col in stats_df.columns:
        col_def: dict = {"field": col, "headerName": col}
        if col not in ("property", "period"):
            col_def["valueFormatter"] = {"function": formatter}
        column_defs.append(col_def)
    return dag.AgGrid(
        id=grid_id,
        rowData=stats_df.to_dict("records"),
        columnDefs=column_defs,
        defaultColDef={"resizable": False, "sortable": False},
        columnSize="responsiveSizeToFit",
        # Symbol column names contain dots (RUS_CBR.RATE); without this AG Grid
        # resolves them as nested paths and renders empty cells.
        dashGridOptions={"domLayout": "autoHeight", "suppressFieldDotNotation": True},
        style={"height": None},
    )

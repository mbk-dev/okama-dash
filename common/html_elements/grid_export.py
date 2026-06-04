"""
CSV export helper for dash-ag-grid components.

Provides a reusable export button and callback function.
"""

import dash_bootstrap_components as dbc


def create_csv_export_button(button_id: str) -> dbc.Button:
    """
    Create a CSV export button styled per AGENTS.md conventions (inline action).

    Args:
        button_id: Unique ID for the button element.

    Returns:
        dbc.Button configured for CSV export trigger.
    """
    return dbc.Button(
        "Export CSV",
        id=button_id,
        color="secondary",
        outline=True,
        size="sm",
    )


def csv_export_callback(n_clicks):
    """
    Callback function that triggers CSV export when clicked.

    Use this as a callback body with Output(<grid_id>, "exportDataAsCsv")
    and Input(<button_id>, "n_clicks").

    Args:
        n_clicks: Button click count.

    Returns:
        True to trigger export, False otherwise.
    """
    if n_clicks:
        return True
    return False

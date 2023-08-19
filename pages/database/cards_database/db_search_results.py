import dash_bootstrap_components as dbc
from dash import html, dcc, callback, ALL, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import okama as ok

card_db_search_results = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.Div(id="db-search-results-div"),
                ]
            )
        ]
    ),
    class_name="mb-3",
)


@callback(
    Output("db-search-results-div", "children"),
    Input("db-search-button", "n_clicks"),
    State("db-search-input", "value"),  # text to search
    State("db-search-namespace", "value"),  # namespace
    prevent_initial_call=True,
)
def db_search(n_clicks: int, text_to_search: str, namespace: str) -> dash_table.DataTable:
    search_df = ok.search(text_to_search, namespace=namespace if namespace != "ANY" else None).drop(
        columns=["ticker"], errors="ignore"
    )
    if search_df.empty:
        output = "Not found in the database ..." if namespace == "ANY" else f"Not found in {namespace} namespace ..."
    else:
        output = dash_table.DataTable(
            data=search_df.to_dict(orient="records"),
            style_data={
                "whiteSpace": "normal",
                "height": "auto",
            },
            page_size=15,
        )
    return output

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import html, callback
from dash.dependencies import Input, Output, State

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
def db_search(n_clicks: int, text_to_search: str, namespace: str) -> str | dag.AgGrid:
    if not text_to_search or not text_to_search.strip():
        # A blank query (untouched field → value is None) must not reach okama:
        # ok.search(None) does df[...].str.contains(None) → re.compile(None) → TypeError.
        return "Enter a search query ..."
    search_df = ok.search(text_to_search, namespace=namespace if namespace != "ANY" else None).drop(
        columns=["ticker"], errors="ignore"
    )
    if search_df.empty:
        output = "Not found in the database ..." if namespace == "ANY" else f"Not found in {namespace} namespace ..."
    else:
        output = dag.AgGrid(
            rowData=search_df.to_dict("records"),
            columnDefs=[{"field": c} for c in search_df.columns],
            defaultColDef={"resizable": False, "sortable": False},
            columnSize="responsiveSizeToFit",
            dashGridOptions={"pagination": True, "paginationPageSize": 15, "domLayout": "autoHeight"},
            style={"height": None},
        )
    return output

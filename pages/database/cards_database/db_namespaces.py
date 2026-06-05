import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import html

import pandas as pd
import okama as ok

column1_name = "Namespaces"
column2_name = "Description"

namespaces_df = pd.DataFrame.from_dict(ok.namespaces, orient="index").reset_index(names=column1_name)
namespaces_df = namespaces_df.rename(columns={0: column2_name})
namespaces_df = namespaces_df[[column1_name, column2_name]]

db_namespaces_table = dag.AgGrid(
    rowData=namespaces_df.to_dict("records"),
    columnDefs=[{"field": column1_name}, {"field": column2_name}],
    defaultColDef={"resizable": False, "sortable": False},
    columnSize="responsiveSizeToFit",
    dashGridOptions={"domLayout": "autoHeight"},
    style={"height": None},
)

card_db_namespaces = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Okama namespaces"),
                    db_namespaces_table,
                ]
            )
        ]
    ),
    class_name="mb-3",
)

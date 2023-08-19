from typing import Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash.dependencies import Input, Output, State
from dash import html, dcc, callback, ALL, MATCH, dash_table

import pandas as pd
import okama as ok

column1_name = "Namespaces"
column2_name = "Description"

namespaces_df = pd.DataFrame.from_dict(ok.namespaces, orient="index").reset_index(names=column1_name)
namespaces_df.rename(columns={0: column2_name}, inplace=True)
namespaces_df = namespaces_df[[column1_name, column2_name]]

db_namespaces_table = dash_table.DataTable(
    data=namespaces_df.to_dict(orient="records"),
    style_data={
        "whiteSpace": "normal",
        "height": "auto",
    },
    style_table={"overflowX": "auto"},
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

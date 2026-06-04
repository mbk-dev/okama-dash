import dash_bootstrap_components as dbc
from dash import html

from common.html_elements.grid_export import create_csv_export_button

card_table = dbc.Card(
    dbc.CardBody(
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.H4(children="Statistics table"), width="auto"),
                        dbc.Col(
                            create_csv_export_button("al-statistics-export-btn"),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    class_name="mb-2",
                ),
                html.Div(id="al-describe-table"),
            ]
        )
    ),
    class_name="mb-3",
)

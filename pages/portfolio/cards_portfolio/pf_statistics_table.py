import dash_bootstrap_components as dbc
from dash import dcc, html

from common.html_elements.grid_export import create_xlsx_export_button

card_table = dbc.Card(
    dbc.CardBody(
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(html.H4(children="Statistics table"), width="auto"),
                        dbc.Col(
                            create_xlsx_export_button("pf-statistics-export-btn"),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    class_name="mb-2",
                ),
                dcc.Download(id="pf-statistics-download"),
                # Downloads for the dynamically rendered MC forecast grids live here
                # statically, so their export callbacks always have a valid Output target.
                dcc.Download(id="pf-survival-statistics-download"),
                dcc.Download(id="pf-wealth-statistics-download"),
                html.P("Portfolio statistics without cash flows:"),
                html.Div(id="pf-describe-table"),
            ]
        )
    ),
    class_name="mb-3",
)

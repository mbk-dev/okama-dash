import dash_bootstrap_components as dbc
import okama
from dash import html, dcc

search_desc = "Search in assets (stocks, ETF, mutual funds, currencies, commodities) or indexes"

card_db_search_controls = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Search Database"),
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Label(search_desc),
                                        lg=8,
                                        md=8,
                                        sm=12,
                                    ),
                                    dbc.Col(
                                        html.Label("Namespace"),
                                        lg=4,
                                        md=4,
                                        sm=12,
                                    ),
                                ]
                            ),
                            html.Div(
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="db-search-input",
                                                    placeholder="Text to search",
                                                    type="text",
                                                ),
                                                lg=8,
                                                md=8,
                                                sm=12,
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="db-search-namespace",
                                                    multi=False,
                                                    options=["ANY"] + okama.assets_namespaces,
                                                    value="ANY",
                                                    placeholder="Select a Namespace",
                                                ),
                                                lg=4,
                                                md=4,
                                                sm=12,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [dbc.Button("Search", id="db-search-button", n_clicks=0, color="primary")],
                                            style={"text-align": "center"},
                                            className="p-3",
                                        )
                                    ),
                                ]
                            ),
                        ],
                    ),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

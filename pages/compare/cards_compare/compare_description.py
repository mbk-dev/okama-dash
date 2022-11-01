import dash_bootstrap_components as dbc
from dash import html

from pages.compare.cards_compare.eng.compare_description_txt import compare_description_text

card_compare_description = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Compare Assets widget"),
                    html.Div(compare_description_text),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

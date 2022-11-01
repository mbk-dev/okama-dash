import dash_bootstrap_components as dbc
from dash import html

from pages.efficient_frontier.cards_efficient_frontier.eng.ef_description_txt import ef_description_text

card_ef_description = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Efficient Frontier widget"),
                    html.Div(ef_description_text),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

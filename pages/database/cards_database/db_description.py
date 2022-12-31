import dash_bootstrap_components as dbc
from dash import html

from pages.database.cards_database.eng.db_description_txt import db_description_text

card_db_description = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Financial Database"),
                    html.Div(db_description_text),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

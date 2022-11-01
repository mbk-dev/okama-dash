import dash_bootstrap_components as dbc
from dash import html

from pages.portfolio.cards_portfolio.eng.portfolio_description_txt import portfolio_description_text

card_portfolio_description = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H4(children="Investment Portfolio widget"),
                    html.Div(portfolio_description_text),
                ]
            )
        ]
    ),
    class_name="mb-3",
)

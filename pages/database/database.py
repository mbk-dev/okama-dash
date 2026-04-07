import warnings

import dash
import dash_bootstrap_components as dbc
from pages.database.cards_database.db_description import card_db_description
from pages.database.cards_database.db_namespaces import card_db_namespaces
from pages.database.cards_database.db_search_controls import card_db_search_controls
from pages.database.cards_database.db_search_results import card_db_search_results

warnings.simplefilter(action="ignore", category=FutureWarning)

dash.register_page(
    __name__,
    path="/database",
    title="Search financial database : okama",
    name="Database",
    description="Okama financial database - free historical data for stocks, etf, mutual funds, indexes, currencies, commodities, rates etc.",
)


def layout():
    page = dbc.Container(
        [
            dbc.Row(dbc.Col(card_db_search_controls, width=12), align="center"),
            dbc.Row(dbc.Col(card_db_search_results, width=12), align="center"),
            dbc.Row(dbc.Col(card_db_namespaces, width=12), align="center"),
            dbc.Row(dbc.Col(card_db_description, width=12), align="left"),
        ],
        class_name="mt-2",
        fluid="md",
    )
    return page

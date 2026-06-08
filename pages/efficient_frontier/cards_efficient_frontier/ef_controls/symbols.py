"""Efficient Frontier tickers MultiSelect: the builder plus the search and
asset-count-disable callbacks."""

import dash_mantine_components as dmc
from dash import html, callback
from dash.dependencies import Input, Output

from common import settings as settings
from common.mantine import search_provider
from common.symbols import get_selected_symbol_options, search_symbol_options


def symbols_select(tickers):
    return html.Div(
        [
            html.Label("Tickers in the Efficient Frontier"),
            search_provider(
                dmc.MultiSelect(
                    data=get_selected_symbol_options(tickers if tickers else settings.default_symbols),
                    value=tickers if tickers else settings.default_symbols,
                    placeholder="Select assets",
                    id="ef-symbols-list",
                    searchable=True,
                    clearable=False,
                    nothingFoundMessage="No matching tickers",
                    comboboxProps={"shadow": "md"},
                )
            ),
        ],
    )


@callback(
    Output("ef-symbols-list", "data"),
    Input("ef-symbols-list", "searchValue"),
    Input("ef-symbols-list", "value"),
)
def optimize_search_ef(search_value, selected_values):
    return search_symbol_options(search_value, selected_values)


@callback(
    Output("ef-symbols-list", "disabled"),
    Input("ef-symbols-list", "value"),
)
def disable_search(tickers_list) -> bool:
    """
    Disable asset search form if the number of ticker exceeds allowed in settings.
    """
    return len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS

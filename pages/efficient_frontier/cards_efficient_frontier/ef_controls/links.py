"""Shareable-link callback for the Efficient Frontier card."""

from dash import callback
from dash.dependencies import Input, Output

from common.create_link import create_link


@callback(
    Output("ef-show-url", "children"),
    Input("ef-url", "href"),
    Input("ef-symbols-list", "value"),
    Input("ef-base-currency", "value"),
    Input("ef-first-date", "value"),
    Input("ef-last-date", "value"),
    Input("ef-rebalancing-frequency", "value"),
)
def update_link_ef(href: str, tickers_list: list, ccy: str, first_date: str, last_date: str, rebal: str):
    return create_link(
        ccy=ccy,
        first_date=first_date,
        href=href,
        last_date=last_date,
        tickers_list=tickers_list,
        rebal=rebal,
    )

"""Assembles the Efficient Frontier controls card from the per-feature sections
(symbols / options) plus the small generic rows below; the section callbacks
live in their own modules."""

from typing import Optional

import dash_bootstrap_components as dbc
from dash import html, dcc

from common import inflation as inflation
from common.html_elements.copy_link_div import create_copy_link_div
from common.html_elements.submit_spinner import create_submit_spinner
from common.date_input import current_month, date_input, register_date_validation
import pages.efficient_frontier.cards_efficient_frontier.eng.ef_tooltips_options_txt as tl
from .symbols import symbols_select
from .options import options_section


def _currency_rebal_section(ccy, rebal_value, currency_list):
    return html.Div(
        [
            html.Label("Base currency"),
            dcc.Dropdown(
                options=currency_list,
                # URL values are normalized and validated: dcc.Dropdown
                # silently clears a value missing from its options.
                value=inflation.resolve_url_currency(ccy, currency_list),
                multi=False,
                clearable=False,
                placeholder="Select a base currency",
                id="ef-base-currency",
            ),
            html.Label("Rebalancing Frequency"),
            dcc.Dropdown(
                options=[
                    {"label": "year", "value": "year"},
                    {"label": "half-year", "value": "half-year"},
                    {"label": "quarter", "value": "quarter"},
                    {"label": "month", "value": "month"},
                    {"label": "none", "value": "none"},
                ],
                value=rebal_value,
                multi=False,
                clearable=False,
                placeholder="Select rebalancing frequency",
                id="ef-rebalancing-frequency",
            ),
        ],
    )


def _dates_row(first_date, last_date):
    return dbc.Row(
        [
            dbc.Col(
                [html.Label("First Date")]
                + date_input("ef-first-date", first_date if first_date else "2000-01"),
            ),
            dbc.Col(
                [html.Label("Last Date")]
                + date_input("ef-last-date", last_date if last_date else current_month()),
            ),
        ]
    )


def _copy_link_row():
    return dbc.Row(
        # copy link to clipboard button
        create_copy_link_div(
            location_id="ef-url",
            hidden_div_with_url_id="ef-show-url",
            button_id="ef-copy-link-button",
            card_name="Efficient Frontier",
        )
    )


def _transition_map_section():
    """The 'Transition map' header and toggle. Returns a list of sibling rows so
    it can be splatted into the controls card without adding a wrapper element."""
    return [
        dbc.Row(html.H6(children="Transition map")),
        dbc.Row(
            [
                dbc.Label(
                    [
                        "Show transition map",
                        html.I(
                            className="bi bi-info-square ms-2",
                            id="info-transition-map",
                        ),
                    ],
                    width=6,
                ),
                dbc.Tooltip(
                    tl.ef_options_transition_map,
                    target="info-transition-map",
                ),
                dbc.RadioItems(
                    options=[
                        {"label": "On", "value": "On"},
                        {"label": "Off", "value": "Off"},
                    ],
                    value="Off",
                    id="transition-map-option",
                ),
            ],
            className="p-1",
        ),
    ]


def _submit_row():
    return html.Div(
        [
            dbc.Button(
                children="Submit",
                id="ef-submit-button-state",
                n_clicks=0,
                color="primary",
            ),
            create_submit_spinner("ef-submit-spinner"),
        ],
        style={"textAlign": "center"},
        className="p-3",
    )


def card_controls(
    tickers: Optional[list],
    first_date: Optional[str],
    last_date: Optional[str],
    ccy: Optional[str],
    rebal: Optional[str],
):
    rebal_options = {"year", "half-year", "quarter", "month", "none"}
    rebal_from_url = rebal.lower() if isinstance(rebal, str) else None
    rebal_value = rebal_from_url if rebal_from_url in rebal_options else "month"
    currency_list = inflation.get_currency_list()

    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Efficient Frontier", className="card-title"),
                symbols_select(tickers),
                _currency_rebal_section(ccy, rebal_value, currency_list),
                html.Div(
                    [
                        _dates_row(first_date, last_date),
                        _copy_link_row(),
                        *options_section(tickers),
                        *_transition_map_section(),
                    ]
                ),
                _submit_row(),
            ]
        ),
        class_name="mb-3",
    )
    return card


register_date_validation("ef-first-date")
register_date_validation("ef-last-date")

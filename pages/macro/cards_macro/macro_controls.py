"""Control-bar building blocks shared by all macro pages.

Macro pages use a compact one-row control bar above the chart (chart-first
template, spec section 4) instead of the controls-card/info-card pair. Each
page assembles its own dbc.Row from these column factories; the row uses
Bootstrap gutters (g-2) so controls keep the standard gap when the bar wraps
on narrow screens.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from common.date_input import date_input
from common.html_elements.submit_spinner import create_submit_spinner
from common.mantine import search_provider


def options_from_catalog(catalog: dict[str, str]) -> list[dict]:
    return [{"label": label, "value": symbol} for symbol, label in catalog.items()]


def series_multiselect_column(page_prefix: str, catalog: dict[str, str], selected: list[str]) -> dbc.Col:
    return dbc.Col(
        [
            html.Label("Series"),
            search_provider(
                dmc.MultiSelect(
                    data=options_from_catalog(catalog),
                    value=selected,
                    id=f"{page_prefix}-series",
                    searchable=True,
                    clearable=False,
                    nothingFoundMessage="No matching series",
                    comboboxProps={"shadow": "md"},
                )
            ),
        ],
        lg=4,
        md=6,
        sm=12,
    )


def date_columns(page_prefix: str, first_date: str, last_date: str) -> list[dbc.Col]:
    return [
        dbc.Col(
            [html.Label("First Date")] + date_input(f"{page_prefix}-first-date", first_date),
            lg=2,
            md=3,
            sm=6,
        ),
        dbc.Col(
            [html.Label("Last Date")] + date_input(f"{page_prefix}-last-date", last_date),
            lg=2,
            md=3,
            sm=6,
        ),
    ]


def submit_button_column(page_prefix: str, label: str = "Submit") -> dbc.Col:
    return dbc.Col(
        html.Div(
            [
                dbc.Button(label, id=f"{page_prefix}-submit-button", n_clicks=0, color="primary"),
                create_submit_spinner(f"{page_prefix}-submit-spinner"),
            ]
        ),
        width="auto",
        class_name="ms-auto",
    )


def make_submit_guard():
    """Disable-submit predicate: True (disabled) when no series are selected."""

    def guard(selected: list | None) -> bool:
        return not selected

    return guard

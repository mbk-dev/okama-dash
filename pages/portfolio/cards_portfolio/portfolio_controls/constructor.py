"""Ticker | Weight constructor: the dynamic asset-row block, its row builder and
the callbacks that add/remove rows, search tickers, validate weights and sum
them."""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
from dash import html, callback, ALL, MATCH
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from common.mantine import search_provider
from common.symbols import get_selected_symbol_options, search_symbol_options


def tickers_weights_block():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.Label("Tickers"), width=6),
                    dbc.Col(html.Label("Weights"), width=6),
                ],
            ),
            html.Div(id="dynamic-container", children=[], className="vstack gap-2"),
            dbc.Row(
                [
                    dbc.Col(dbc.Button("Add Asset", id="dynamic-add-filter", n_clicks=0)),
                    dbc.Col(html.Div(id="pf-portfolio-weights-sum")),
                ]
            ),
        ],
        className="vstack gap-2",
    )


@callback(
    Output({"type": "pf-dynamic-input", "index": MATCH}, "invalid"),
    Input({"type": "pf-dynamic-input", "index": MATCH}, "value"),
)
def validate_weight_input(value) -> bool:
    """Flag a portfolio weight as invalid when it is outside 0-100."""
    if value in (None, ""):
        return False
    return not 0 <= float(value) <= 100


# ----------------------- Ticker | Weight constructor -------------------------------------------
@callback(
    Output("dynamic-container", "children"),
    Input("pf_tickers_url", "data"),
    Input("pf_weights_url", "data"),
    Input("dynamic-add-filter", "n_clicks"),
    Input({"type": "pf-dynamic-remove", "index": ALL}, "n_clicks"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "id"),
    State({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    State({"type": "pf-dynamic-input", "index": ALL}, "value"),
)
def update_rows_in_constructor(
    tickers, weights, n_clicks, remove_clicks, dropdown_ids, selected_tickers, selected_weights
):
    trigger = dash.ctx.triggered_id

    if trigger == "pf_tickers_url" or trigger == "pf_weights_url" or not dropdown_ids:
        rows = get_constructor_rows_from_url(tickers, weights)
    else:
        rows = get_current_constructor_rows(dropdown_ids, selected_tickers, selected_weights)
        if trigger == "dynamic-add-filter":
            next_index = max((row["index"] for row in rows), default=-1) + 1
            rows.append({"index": next_index, "symbol": None, "weight": None})
        elif isinstance(trigger, dict) and trigger.get("type") == "pf-dynamic-remove":
            rows = [row for row in rows if row["index"] != trigger["index"]]
            if not rows:
                next_index = max((row_id["index"] for row_id in dropdown_ids), default=-1) + 1
                rows = [{"index": next_index, "symbol": None, "weight": None}]

    return [
        append_row(row["index"], row["symbol"], row["weight"], get_weight_placeholder(rows, idx))
        for idx, row in enumerate(rows)
    ]


def get_constructor_rows_from_url(tickers, weights):
    tickers = tickers or []
    weights = weights or []
    row_count = max(len(tickers), len(weights), 1)
    return [
        {
            "index": index,
            "symbol": tickers[index] if index < len(tickers) else None,
            "weight": weights[index] if index < len(weights) else None,
        }
        for index in range(row_count)
    ]


def get_current_constructor_rows(dropdown_ids, selected_tickers, selected_weights):
    return [
        {
            "index": row_id["index"],
            "symbol": ticker,
            "weight": weight,
        }
        for row_id, ticker, weight in zip(dropdown_ids, selected_tickers, selected_weights, strict=True)
    ]


def get_weight_placeholder(rows, row_position):
    previous_weights_sum = sum(float(row["weight"]) for row in rows[:row_position] if row["weight"] is not None)
    remaining_weight = max(0, np.around(100 - previous_weights_sum, decimals=3))
    return f"0 - {remaining_weight:g}"


def append_row(row_index, symbol, weight, weight_placeholder):
    return dbc.Row(
        [
            dbc.Col(
                search_provider(
                    dmc.Select(
                        id={"type": "pf-dynamic-dropdown", "index": row_index},
                        data=get_selected_symbol_options([symbol] if symbol else None),
                        value=symbol,
                        placeholder="Type a ticker",
                        searchable=True,
                        clearable=True,
                        nothingFoundMessage="No matching tickers",
                        comboboxProps={"shadow": "md"},
                    )
                ),
                width=6,
            ),
            dbc.Col(
                dbc.Input(
                    id={"type": "pf-dynamic-input", "index": row_index},
                    placeholder=weight_placeholder,
                    value=weight,
                    type="number",
                    min=0,
                    max=100,
                ),
            ),
            # "auto" + ps-1 keeps the remove icon snug against the input
            # (same compact style as the CWD threshold rows)
            dbc.Col(
                dbc.Button(
                    html.I(className="bi bi-x-lg"),
                    id={"type": "pf-dynamic-remove", "index": row_index},
                    color="link",
                    class_name="p-0 text-secondary",
                    size="sm",
                    title="Remove asset",
                ),
                width="auto",
                class_name="ps-1 d-flex align-items-center",
            ),
        ],
    )


@callback(
    Output({"type": "pf-dynamic-dropdown", "index": MATCH}, "data"),
    Input({"type": "pf-dynamic-dropdown", "index": MATCH}, "searchValue"),
    Input({"type": "pf-dynamic-dropdown", "index": MATCH}, "value"),
)
def optimize_search_al(search_value, selected_value) -> list:
    if not search_value:
        raise PreventUpdate
    return search_symbol_options(search_value, [selected_value] if selected_value else None)


@callback(
    Output("pf-portfolio-weights-sum", "children"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
)
def print_weights_sum(values) -> str:
    # Single children Output: returning a (text, flag) tuple would serialize the
    # whole tuple into children and leak a bare bool — an invalid ReactNode.
    weights_sum = sum(float(x) for x in values if x)
    return f"Total: {np.around(weights_sum, decimals=3)}"

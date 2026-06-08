"""Custom cash flows (TimeSeries) — layout, dynamic rows and callbacks.

okama's base CashFlow accepts time_series_dic for every strategy, so one-off
user entries combine with the regular flow. The block mirrors the Find-max-
withdrawal element: a clickable chevron header + dbc.Collapse. For the
time_series strategy the block IS the strategy (its header is hidden, the body
keeps the former plain bordered look).
"""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, callback, ALL, MATCH
from dash.dependencies import Input, Output, State

from common.date_input import register_date_validation
from common.mantine import search_provider
from .constants import MAX_TIMESERIES_ENTRIES, TS_DEFAULT_DATE, TS_DEFAULT_AMOUNT
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def _build_initial_ts_rows(cf_ts):
    if not cf_ts:
        return []
    rows = []
    for i, (date, amount) in enumerate(cf_ts[:MAX_TIMESERIES_ENTRIES]):
        try:
            amount_val = float(amount)
        except (ValueError, TypeError):
            amount_val = None
        rows.append({"index": i, "date": date, "amount": amount_val})
    return rows


def _ts_collapse_is_open(cf_strategy, ts_rows) -> bool:
    """Open the Custom cash flows collapse for the time_series strategy
    (the block IS the strategy) or when rows were prefilled from the URL."""
    return cf_strategy == "time_series" or bool(ts_rows)


def _chevron_class(is_open: bool) -> str:
    """Bootstrap-icon class for the collapse chevron, matching the
    Find-max-withdrawal toggle."""
    return "bi bi-chevron-down me-2" if is_open else "bi bi-chevron-right me-2"


def _ts_toggle_style(cf_strategy) -> dict:
    """Hide the Custom cash flows header for the time_series strategy (the
    dropdown already names it "Custom Time Series" and the block IS that
    strategy's only input); show the clickable header otherwise."""
    if cf_strategy == "time_series":
        return {"display": "none"}
    return {"cursor": "pointer", "userSelect": "none"}


def _ts_body_class(cf_strategy) -> str:
    """Plain bordered block for the headerless time_series strategy (unchanged
    from the former accordion look); a chrome-less Find-style body otherwise."""
    if cf_strategy == "time_series":
        return "vstack gap-2 border rounded bg-body-tertiary p-3"
    return "vstack gap-2 p-2"


def _ts_row(index, date_val=None, amount_val=None):
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Input(
                        id={"type": "pf-cf-ts-date", "index": index},
                        type="text",
                        placeholder="2020-01",
                        value=date_val,
                    ),
                    dbc.FormFeedback("Use YYYY-MM format", type="invalid"),
                ],
                width=5,
            ),
            dbc.Col(
                search_provider(
                    dmc.NumberInput(
                        id={"type": "pf-cf-ts-amount", "index": index},
                        placeholder="-1 000",
                        value=amount_val,
                        thousandSeparator=" ",
                    )
                ),
                width=5,
            ),
            dbc.Col(
                dbc.Button(
                    html.I(className="bi bi-x-lg"),
                    id={"type": "pf-cf-ts-remove", "index": index},
                    color="link",
                    class_name="p-0 text-secondary",
                    size="sm",
                ),
                width=2,
                class_name="d-flex justify-content-center",
            ),
        ],
        class_name="mb-1",
    )


def _custom_cashflows_block(cf_strategy=None, cf_ts=None):
    # okama's base CashFlow accepts time_series_dic for every strategy, so
    # one-off user entries combine with the regular flow. Mirrors the
    # Find-max-withdrawal element above: a clickable chevron header +
    # dbc.Collapse. Initially collapsed; expanded for time_series (the
    # block IS that strategy — its header is hidden, the body keeps the
    # former plain bordered look) and for URL-prefilled entries.
    ts_initial_rows = _build_initial_ts_rows(cf_ts)
    ts_is_open = _ts_collapse_is_open(cf_strategy, ts_initial_rows)
    return html.Div(
        [
            html.Div(
                [
                    html.I(className=_chevron_class(ts_is_open), id="pf-cf-ts-chevron"),
                    "Custom cash flows",
                    html.I(className="bi bi-info-square ms-2", id="pf-info-cf-ts"),
                    dbc.Tooltip(tl.pf_cf_time_series, target="pf-info-cf-ts"),
                ],
                id="pf-cf-ts-toggle",
                n_clicks=0,
                className="fw-bold",
                style=_ts_toggle_style(cf_strategy),
            ),
            dbc.Collapse(
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Label("Date (YYYY-MM)"), width=5),
                                dbc.Col(html.Label("Amount"), width=5),
                                dbc.Col(width=2),
                            ],
                        ),
                        html.Div(
                            id="pf-cf-ts-container",
                            children=[_ts_row(r["index"], r["date"], r["amount"]) for r in ts_initial_rows],
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button(
                                    "Add Entry", id="pf-cf-ts-add", n_clicks=0, size="sm", color="secondary"
                                ),
                            ),
                            class_name="mt-1",
                        ),
                        dbc.FormText(
                            f"Negative amounts = withdrawals, positive = contributions "
                            f"(max {MAX_TIMESERIES_ENTRIES} entries)"
                        ),
                    ],
                    id="pf-cf-ts-body",
                    className=_ts_body_class(cf_strategy),
                ),
                id="pf-cf-ts-collapse",
                is_open=ts_is_open,
            ),
        ],
        id="pf-cf-ts-block",
        className="mt-3",
    )


@callback(
    Output("pf-cf-ts-collapse", "is_open", allow_duplicate=True),
    Output("pf-cf-ts-chevron", "className", allow_duplicate=True),
    Output("pf-cf-ts-toggle", "style"),
    Output("pf-cf-ts-body", "className"),
    Input("pf-cf-strategy-type", "value"),
    prevent_initial_call=True,
)
def set_ts_collapse_for_strategy(strategy):
    """Force-open the Custom cash flows collapse and hide its header when
    switching to time_series (the block IS that strategy's only input); collapse
    it and restore the clickable Find-style header for any other strategy."""
    is_open = strategy == "time_series"
    return is_open, _chevron_class(is_open), _ts_toggle_style(strategy), _ts_body_class(strategy)


@callback(
    Output("pf-cf-ts-collapse", "is_open"),
    Output("pf-cf-ts-chevron", "className"),
    Input("pf-cf-ts-toggle", "n_clicks"),
    State("pf-cf-ts-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_ts_collapse(n_clicks, is_open):
    """Flip the Custom cash flows collapse and its chevron, mirroring the
    Find-max-withdrawal toggle."""
    new_open = not is_open
    return new_open, _chevron_class(new_open)


@callback(
    Output("pf-cf-ts-container", "children"),
    Input("pf-cf-ts-add", "n_clicks"),
    Input({"type": "pf-cf-ts-remove", "index": ALL}, "n_clicks"),
    Input("pf-cf-ts-collapse", "is_open"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "id"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-amount", "index": ALL}, "value"),
    State("pf-cf-strategy-type", "value"),
)
def manage_ts_rows(add_clicks, remove_clicks, is_open, ids, dates, amounts, strategy):
    trigger = dash.ctx.triggered_id
    rows = []
    if ids:
        for row_id, d, a in zip(ids, dates, amounts, strict=True):
            rows.append({"index": row_id["index"], "date": d, "amount": a})

    if isinstance(trigger, dict) and trigger.get("type") == "pf-cf-ts-remove":
        rows = [r for r in rows if r["index"] != trigger["index"]]
    elif trigger == "pf-cf-ts-add" and len(rows) < MAX_TIMESERIES_ENTRIES:
        next_idx = max((r["index"] for r in rows), default=-1) + 1
        rows.append({"index": next_idx, "date": None, "amount": None})

    # An empty visible block starts with one row: the example withdrawal for
    # the time_series strategy (the block IS the strategy), a blank row for
    # every other strategy — there the regular flow already exists and a
    # prefilled example would silently join the calculation. While the
    # collapse is closed the container stays empty.
    if not rows and is_open:
        if strategy == "time_series":
            rows = [{"index": 0, "date": TS_DEFAULT_DATE, "amount": TS_DEFAULT_AMOUNT}]
        else:
            rows = [{"index": 0, "date": None, "amount": None}]

    return [_ts_row(r["index"], r["date"], r["amount"]) for r in rows]


@callback(
    Output("pf-cf-ts-add", "disabled"),
    Input({"type": "pf-cf-ts-date", "index": ALL}, "id"),
)
def limit_ts_entries(ids):
    return len(ids) >= MAX_TIMESERIES_ENTRIES


register_date_validation({"type": "pf-cf-ts-date", "index": MATCH})

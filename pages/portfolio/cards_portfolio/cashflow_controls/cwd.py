"""Cut Withdrawals if Drawdown (CWD) strategy — layout, dynamic threshold rows
and callbacks.

Panel visibility is driven by the shared ``toggle_strategy_panels`` callback
(``common.py``) via the ``pf-cf-cwd-panel`` id.
"""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, callback, ALL
from dash.dependencies import Input, Output, State

from common.mantine import search_provider
from .helpers import _prefill_amount
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def _build_initial_cwd_rows(cwd_tr):
    if not cwd_tr:
        return None
    rows = []
    for i, (threshold, reduction) in enumerate(cwd_tr):
        try:
            t_val = float(threshold)
            r_val = float(reduction)
        except (ValueError, TypeError):
            continue
        rows.append({"index": i, "threshold": t_val, "reduction": r_val})
    return rows or None


def _cwd_panel(cwd_amount=None, cwd_indexation=None, cwd_tr=None):
    cwd_initial_rows = _build_initial_cwd_rows(cwd_tr)
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Withdrawal amount",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-cwd-amount",
                                    ),
                                ]
                            ),
                            # NumberInput instead of dbc.Input: an HTML
                            # input[type=number] cannot group digits (#17).
                            search_provider(
                                dmc.NumberInput(
                                    id="pf-cf-cwd-amount",
                                    max=0,
                                    value=_prefill_amount(cwd_amount, 0),
                                    thousandSeparator=" ",
                                    placeholder="-60 000",
                                )
                            ),
                            dbc.FormText("Must be negative or zero"),
                            dbc.Tooltip(
                                tl.pf_cf_cwd_amount,
                                target="pf-info-cwd-amount",
                            ),
                        ],
                        lg=6,
                        md=6,
                        sm=12,
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Indexation rate",
                                    html.I(className="bi bi-info-square ms-2", id="pf-info-cwd-indexation"),
                                ],
                                className="text-nowrap",
                            ),
                            dbc.Tooltip(tl.pf_cf_indexation, target="pf-info-cwd-indexation"),
                            dbc.Input(
                                id="pf-cf-cwd-indexation",
                                type="number",
                                min=0,
                                max=100,
                                step=0.1,
                                value=cwd_indexation,
                                placeholder="inflation",
                            ),
                            dbc.FormText("0 - 100 % (empty = inflation)"),
                        ],
                        lg=6,
                        md=6,
                        sm=6,
                    ),
                ],
                class_name="mt-2",
            ),
            # Bordered block visually separates the drawdown-threshold table
            # from the settings above (withdrawal amount, indexation rate).
            html.Div(
                [
                    html.Div(
                        [
                            "Drawdown thresholds",
                            html.I(className="bi bi-info-square ms-2", id="pf-info-cwd-thresholds"),
                        ],
                        className="fw-semibold mb-2 text-nowrap",
                    ),
                    dbc.Tooltip(tl.pf_cf_cwd_thresholds, target="pf-info-cwd-thresholds"),
                    dbc.Row(
                        [
                            dbc.Col(html.Label("Drawdown threshold (%)", className="text-nowrap"), width=6),
                            dbc.Col(html.Label("Reduction (%)")),
                        ],
                    ),
                    html.Div(
                        id="pf-cf-cwd-container",
                        children=(
                            [_cwd_row(r["index"], r["threshold"], r["reduction"]) for r in cwd_initial_rows]
                            if cwd_initial_rows
                            else []
                        ),
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button(
                                "Add Threshold",
                                id="pf-cf-cwd-add",
                                n_clicks=0,
                                size="sm",
                                color="secondary",
                            ),
                        ),
                        class_name="mt-1",
                    ),
                    dbc.FormText(
                        "e.g. 20% threshold, 40% reduction = if drawdown > 20%, reduce withdrawal by 40%"
                    ),
                ],
                className="border rounded p-3 bg-body-tertiary mt-3",
            ),
        ],
        id="pf-cf-cwd-panel",
        style={"display": "none"},
    )


def next_cwd_placeholder(
    prev_threshold: float | None,
    prev_reduction: float | None,
) -> tuple[int, int]:
    if prev_threshold is None or prev_reduction is None:
        return (20, 40)
    return (min(int(prev_threshold) + 10, 100), min(int(prev_reduction) + 10, 100))


def _cwd_row(index, threshold_val=None, reduction_val=None, threshold_ph="20", reduction_ph="40"):
    return dbc.Row(
        [
            dbc.Col(
                dbc.Input(
                    id={"type": "pf-cf-cwd-threshold", "index": index},
                    type="number",
                    min=0,
                    max=100,
                    step=1,
                    placeholder=threshold_ph,
                    value=threshold_val,
                ),
                width=6,
            ),
            dbc.Col(
                dbc.Input(
                    id={"type": "pf-cf-cwd-reduction", "index": index},
                    type="number",
                    min=0,
                    max=100,
                    step=1,
                    placeholder=reduction_ph,
                    value=reduction_val,
                ),
            ),
            # "auto" + ps-1 keeps the remove icon snug against the input
            # (a fixed grid column left it floating in empty space)
            dbc.Col(
                dbc.Button(
                    html.I(className="bi bi-x-lg"),
                    id={"type": "pf-cf-cwd-remove", "index": index},
                    color="link",
                    class_name="p-0 text-secondary",
                    size="sm",
                ),
                width="auto",
                class_name="ps-1 d-flex align-items-center",
            ),
        ],
        class_name="mb-1",
    )


@callback(
    Output("pf-cf-cwd-container", "children"),
    Input("pf-cf-cwd-add", "n_clicks"),
    Input({"type": "pf-cf-cwd-remove", "index": ALL}, "n_clicks"),
    State({"type": "pf-cf-cwd-threshold", "index": ALL}, "id"),
    State({"type": "pf-cf-cwd-threshold", "index": ALL}, "value"),
    State({"type": "pf-cf-cwd-reduction", "index": ALL}, "value"),
)
def manage_cwd_rows(add_clicks, remove_clicks, ids, thresholds, reductions):
    trigger = dash.ctx.triggered_id
    rows = []
    if ids:
        for row_id, t, r in zip(ids, thresholds, reductions, strict=True):
            rows.append({"index": row_id["index"], "threshold": t, "reduction": r})

    if isinstance(trigger, dict) and trigger.get("type") == "pf-cf-cwd-remove":
        rows = [r for r in rows if r["index"] != trigger["index"]]
    elif trigger == "pf-cf-cwd-add":
        next_idx = max((r["index"] for r in rows), default=-1) + 1
        rows.append({"index": next_idx, "threshold": None, "reduction": None})
    elif not rows:
        rows = [
            {"index": 0, "threshold": 20, "reduction": 40},
            {"index": 1, "threshold": 50, "reduction": 100},
        ]

    result = []
    prev_t, prev_r = None, None
    for r in rows:
        t_ph, r_ph = next_cwd_placeholder(prev_t, prev_r)
        result.append(_cwd_row(r["index"], r["threshold"], r["reduction"], str(t_ph), str(r_ph)))
        if r["threshold"] is not None and r["reduction"] is not None:
            prev_t, prev_r = r["threshold"], r["reduction"]
    return result


def should_disable_cwd_add(thresholds: list, reductions: list) -> bool:
    if not thresholds or not reductions:
        return False
    last_t = thresholds[-1]
    last_r = reductions[-1]
    return last_t is None or last_r is None


@callback(
    Output("pf-cf-cwd-add", "disabled"),
    Input({"type": "pf-cf-cwd-threshold", "index": ALL}, "value"),
    Input({"type": "pf-cf-cwd-reduction", "index": ALL}, "value"),
)
def disable_cwd_add_button(thresholds, reductions):
    return should_disable_cwd_add(thresholds, reductions)

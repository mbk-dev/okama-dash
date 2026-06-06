import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, callback, ALL, MATCH
from dash.dependencies import Input, Output, State

from common import settings as settings
from common.date_input import register_date_validation
from common.mantine import search_provider
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl

STRATEGY_OPTIONS = [
    {"label": "Fixed Amount (Indexation)", "value": "indexation"},
    {"label": "Fixed Percentage", "value": "percentage"},
    {"label": "Custom Time Series", "value": "time_series"},
    {"label": "Vanguard Dynamic Spending (VDS)", "value": "vds"},
    {"label": "Cut Withdrawals if Drawdown (CWD)", "value": "cwd"},
]

FREQUENCY_OPTIONS = [
    {"label": "None", "value": "none"},
    {"label": "Monthly", "value": "month"},
    {"label": "Quarterly", "value": "quarter"},
    {"label": "Half-year", "value": "half-year"},
    {"label": "Yearly", "value": "year"},
]

STRATEGY_DESCRIPTIONS = {
    "indexation": "Regular withdrawals/contributions indexed by a fixed rate or inflation.",
    "percentage": "Withdrawals/contributions as a fixed percentage of portfolio balance.",
    "time_series": "User-defined cash flows with specific dates and amounts.",
    "vds": "Percentage-based withdrawals with floor/ceiling constraints and min/max bounds. Annual only.",
    "cwd": "Reduce withdrawals when portfolio drawdown exceeds thresholds.",
}

MAX_TIMESERIES_ENTRIES = 50

# Example entry shown when the Custom cash flows block opens empty in the
# time_series strategy (the block IS the strategy): one past-dated withdrawal
# the user can edit. Other strategies open the block with a blank row.
TS_DEFAULT_DATE = "2020-01"
TS_DEFAULT_AMOUNT = -1000


def _prefill_amount(value, fallback):
    """Coerce a URL-prefill string to a number for dmc.NumberInput.

    Query params arrive as strings; NumberInput needs a real number to apply
    the thousands separator. Unset (falsy) or unparseable input falls back."""
    if not value:
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return int(number) if number.is_integer() else number


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


def _ts_accordion_active_item(cf_strategy, ts_rows) -> str | None:
    """Open the Custom cash flows accordion for the time_series strategy
    (the block IS the strategy) or when rows were prefilled from the URL."""
    if cf_strategy == "time_series" or ts_rows:
        return "custom-cashflows"
    return None


def _ts_accordion_class(cf_strategy) -> str:
    """Plain-block look for the time_series strategy: the accordion header
    would just repeat the selected strategy name, so `ts-plain` hides it
    (assets/forms.css) and the body shows as the former bordered block."""
    return "mt-3 ts-plain" if cf_strategy == "time_series" else "mt-3"


def cashflow_accordion_item(
    initial_amount=None,
    cashflow=None,
    discount_rate=None,
    cf_strategy=None,
    cf_freq=None,
    cf_amount=None,
    cf_indexation=None,
    cf_pct=None,
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
    cwd_amount=None,
    cwd_indexation=None,
    cwd_tr=None,
    cf_ts=None,
):
    ts_initial_rows = _build_initial_ts_rows(cf_ts)
    cwd_initial_rows = _build_initial_cwd_rows(cwd_tr)
    return dbc.AccordionItem(
        [
            # Strategy type selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Strategy type",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-cf-strategy",
                                    ),
                                ]
                            ),
                            dcc.Dropdown(
                                options=STRATEGY_OPTIONS,
                                value=cf_strategy if cf_strategy else "indexation",
                                multi=False,
                                clearable=False,
                                searchable=False,
                                id="pf-cf-strategy-type",
                            ),
                            dbc.FormText(
                                id="pf-cf-strategy-description",
                                children=STRATEGY_DESCRIPTIONS.get(cf_strategy or "indexation", ""),
                            ),
                            dbc.Tooltip(
                                tl.pf_cf_strategy_type,
                                target="pf-info-cf-strategy",
                            ),
                        ],
                        lg=12,
                        sm=12,
                    ),
                ],
                class_name="mb-2",
            ),
            # Common: Initial amount + Discount rate
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Initial amount",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-initial-amount",
                                    ),
                                ]
                            ),
                            # NumberInput instead of dbc.Input: an HTML
                            # input[type=number] cannot group digits (#17).
                            search_provider(
                                dmc.NumberInput(
                                    id="pf-initial-amount",
                                    value=_prefill_amount(initial_amount, settings.INITIAL_INVESTMENT_DEFAULT),
                                    min=1,
                                    thousandSeparator=" ",
                                )
                            ),
                            dbc.FormText("Positive number"),
                            dbc.Tooltip(
                                tl.pf_options_tooltip_initial_amount,
                                target="pf-info-initial-amount",
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
                                    "Discount rate",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-discount-rate",
                                    ),
                                ]
                            ),
                            dbc.Input(
                                id="pf-discount-rate",
                                type="number",
                                min=0,
                                max=100,
                                step=0.1,
                                value=discount_rate if discount_rate else None,
                                placeholder="inflation",
                            ),
                            dbc.FormText("0 - 100 % (empty = inflation)"),
                            dbc.Tooltip(
                                tl.pf_options_tooltip_discount_rate,
                                target="pf-info-discount-rate",
                            ),
                        ],
                        lg=6,
                        md=6,
                        sm=12,
                    ),
                ],
            ),
            # Common: Frequency
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Cash flow frequency",
                                    html.I(className="bi bi-info-square ms-2", id="pf-info-cf-frequency"),
                                ],
                                className="text-nowrap",
                            ),
                            dbc.Tooltip(tl.pf_cf_frequency, target="pf-info-cf-frequency"),
                            dcc.Dropdown(
                                options=FREQUENCY_OPTIONS,
                                value=cf_freq if cf_freq else "month",
                                multi=False,
                                clearable=False,
                                searchable=False,
                                id="pf-cf-frequency",
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
                                    "Rate",
                                    html.I(className="bi bi-info-square ms-2", id="pf-info-cf-rate"),
                                ],
                                className="text-nowrap",
                            ),
                            dbc.Tooltip(tl.pf_cf_rate, target="pf-info-cf-rate"),
                            dbc.Input(
                                id="pf-withdrawal-rate",
                                disabled=True,
                            ),
                        ],
                        lg=3,
                        md=3,
                        sm=6,
                        id="pf-withdrawal-rate-col",
                    ),
                    # ---- PercentageStrategy: percentage input (shown only for "percentage") ----
                    dbc.Col(
                        [
                            html.Label(
                                [
                                    "Withdrawal/Contribution",
                                    html.I(
                                        className="bi bi-info-square ms-2",
                                        id="pf-info-cf-pct",
                                    ),
                                ],
                                className="text-nowrap",
                            ),
                            dbc.Input(
                                id="pf-cf-percentage",
                                type="number",
                                min=-100,
                                step=1,
                                value=cf_pct if cf_pct else 0,
                                placeholder="-12",
                            ),
                            dbc.FormText("% of portfolio balance per year. Negative = withdrawal"),
                            dbc.Tooltip(
                                tl.pf_cf_percentage,
                                target="pf-info-cf-pct",
                            ),
                        ],
                        lg=6,
                        md=6,
                        sm=12,
                        id="pf-cf-percentage-col",
                        style={"display": "none"},
                    ),
                ],
                class_name="mt-2",
                id="pf-cf-frequency-row",
            ),
            # ---- IndexationStrategy panel ----
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Cash flow amount",
                                            html.I(
                                                className="bi bi-info-square ms-2",
                                                id="pf-info-cf-amount",
                                            ),
                                        ]
                                    ),
                                    search_provider(
                                        dmc.NumberInput(
                                            id="pf-cf-amount",
                                            value=_prefill_amount(cf_amount, _prefill_amount(cashflow, 0)),
                                            thousandSeparator=" ",
                                        )
                                    ),
                                    dbc.FormText("Negative = withdrawal"),
                                    dbc.Tooltip(
                                        tl.pf_options_tooltip_cash_flow,
                                        target="pf-info-cf-amount",
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
                                            html.I(className="bi bi-info-square ms-2", id="pf-info-cf-indexation"),
                                        ],
                                        className="text-nowrap",
                                    ),
                                    dbc.Tooltip(tl.pf_cf_indexation, target="pf-info-cf-indexation"),
                                    dbc.Input(
                                        id="pf-cf-indexation",
                                        type="number",
                                        min=0,
                                        max=100,
                                        step=0.1,
                                        value=cf_indexation,
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
                ],
                id="pf-cf-indexation-panel",
            ),
            # ---- VanguardDynamicSpending panel ----
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Withdrawal percentage",
                                            html.I(
                                                className="bi bi-info-square ms-2",
                                                id="pf-info-vds-pct",
                                            ),
                                        ]
                                    ),
                                    dbc.Input(
                                        id="pf-cf-vds-percentage",
                                        type="number",
                                        min=-100,
                                        max=0,
                                        step=1,
                                        value=vds_pct if vds_pct else 0,
                                        placeholder="-8",
                                    ),
                                    dbc.FormText("Must be negative or zero (%)"),
                                    dbc.Tooltip(
                                        tl.pf_cf_vds_percentage,
                                        target="pf-info-vds-pct",
                                    ),
                                ],
                                lg=6,
                                md=6,
                                sm=12,
                            ),
                        ],
                        class_name="mt-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Min annual withdrawal",
                                            html.I(className="bi bi-info-square ms-2", id="pf-info-vds-min"),
                                        ],
                                        className="text-nowrap",
                                    ),
                                    dbc.Tooltip(tl.pf_cf_vds_min_max, target="pf-info-vds-min"),
                                    dbc.Input(
                                        id="pf-cf-vds-min-withdrawal",
                                        type="number",
                                        min=0,
                                        value=vds_min,
                                        placeholder="40000",
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
                                            "Max annual withdrawal",
                                            html.I(className="bi bi-info-square ms-2", id="pf-info-vds-max"),
                                        ],
                                        className="text-nowrap",
                                    ),
                                    dbc.Tooltip(tl.pf_cf_vds_min_max, target="pf-info-vds-max"),
                                    dbc.Input(
                                        id="pf-cf-vds-max-withdrawal",
                                        type="number",
                                        min=0,
                                        value=vds_max,
                                        placeholder="100000",
                                    ),
                                ],
                                lg=6,
                                md=6,
                                sm=12,
                            ),
                        ],
                        class_name="mt-2",
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Switch(
                                        label="Adjust min/max by indexation",
                                        value=vds_adj_mm if vds_adj_mm is not None else True,
                                        id="pf-cf-vds-adjust-minmax",
                                        class_name="mb-0",
                                    ),
                                    html.I(className="bi bi-info-square ms-2", id="pf-info-vds-adj-mm"),
                                    dbc.Tooltip(tl.pf_cf_vds_adjust_minmax, target="pf-info-vds-adj-mm"),
                                ],
                                className="d-flex align-items-center text-nowrap",
                            ),
                        ),
                        class_name="mt-1",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Floor",
                                            html.I(
                                                className="bi bi-info-square ms-2",
                                                id="pf-info-vds-floor",
                                            ),
                                        ]
                                    ),
                                    dbc.Input(
                                        id="pf-cf-vds-floor",
                                        type="number",
                                        max=0,
                                        step=0.5,
                                        value=vds_floor,
                                        placeholder="-2.5",
                                    ),
                                    dbc.FormText("Negative (%)"),
                                    dbc.Tooltip(
                                        tl.pf_cf_vds_floor_ceiling,
                                        target="pf-info-vds-floor",
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
                                            "Ceiling",
                                            html.I(
                                                className="bi bi-info-square ms-2",
                                                id="pf-info-vds-ceil",
                                            ),
                                        ]
                                    ),
                                    dbc.Input(
                                        id="pf-cf-vds-ceiling",
                                        type="number",
                                        min=0,
                                        step=0.5,
                                        value=vds_ceil,
                                        placeholder="5",
                                    ),
                                    dbc.FormText("Positive (%)"),
                                    dbc.Tooltip(
                                        tl.pf_cf_vds_floor_ceiling,
                                        target="pf-info-vds-ceil",
                                    ),
                                ],
                                lg=6,
                                md=6,
                                sm=12,
                            ),
                        ],
                        class_name="mt-2",
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Switch(
                                        label="Adjust floor/ceiling by indexation",
                                        value=vds_adj_fc if vds_adj_fc is not None else False,
                                        id="pf-cf-vds-adjust-fc",
                                        class_name="mb-0",
                                    ),
                                    html.I(className="bi bi-info-square ms-2", id="pf-info-vds-adj-fc"),
                                    dbc.Tooltip(tl.pf_cf_vds_adjust_fc, target="pf-info-vds-adj-fc"),
                                ],
                                className="d-flex align-items-center text-nowrap",
                            ),
                        ),
                        class_name="mt-1",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        [
                                            "Indexation rate",
                                            html.I(className="bi bi-info-square ms-2", id="pf-info-vds-indexation"),
                                        ],
                                        className="text-nowrap",
                                    ),
                                    dbc.Tooltip(tl.pf_cf_vds_indexation, target="pf-info-vds-indexation"),
                                    dbc.Input(
                                        id="pf-cf-vds-indexation",
                                        type="number",
                                        min=0,
                                        max=100,
                                        step=0.1,
                                        value=vds_indexation,
                                        placeholder="inflation",
                                    ),
                                    dbc.FormText("0 - 100 % (empty = inflation)"),
                                ],
                                lg=6,
                                md=6,
                                sm=12,
                            ),
                        ],
                        class_name="mt-2",
                    ),
                ],
                id="pf-cf-vds-panel",
                style={"display": "none"},
            ),
            # ---- CutWithdrawalsIfDrawdown panel ----
            html.Div(
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
                                    dbc.Input(
                                        id="pf-cf-cwd-amount",
                                        type="number",
                                        max=0,
                                        value=cwd_amount if cwd_amount else 0,
                                        placeholder="-60000",
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
            ),
            # ---- Custom cash flows (shared across all strategies) ----
            # okama's base CashFlow accepts time_series_dic for every strategy,
            # so one-off user entries combine with the regular flow. Initially
            # collapsed; expanded for time_series (the block IS the strategy)
            # and for URL-prefilled entries.
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            dbc.Tooltip(tl.pf_cf_time_series, target="pf-info-cf-ts"),
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
                        title=[
                            "Custom cash flows",
                            html.I(className="bi bi-info-square ms-2", id="pf-info-cf-ts"),
                        ],
                        item_id="custom-cashflows",
                    ),
                ],
                id="pf-cf-ts-accordion",
                start_collapsed=True,
                active_item=_ts_accordion_active_item(cf_strategy, ts_initial_rows),
                class_name=_ts_accordion_class(cf_strategy),
            ),
        ],
        title="Cash Flow Strategy",
        item_id="cashflow",
    )


# --- Callbacks ---


@callback(
    Output("pf-cf-strategy-description", "children"),
    Output("pf-cf-indexation-panel", "style"),
    Output("pf-cf-percentage-col", "style"),
    Output("pf-cf-vds-panel", "style"),
    Output("pf-cf-cwd-panel", "style"),
    Input("pf-cf-strategy-type", "value"),
)
def toggle_strategy_panels(strategy):
    show = None
    hide = {"display": "none"}
    panels = {
        "indexation": (show, hide, hide, hide),
        "percentage": (hide, show, hide, hide),
        "time_series": (hide, hide, hide, hide),
        "vds": (hide, hide, show, hide),
        "cwd": (hide, hide, hide, show),
    }
    styles = panels.get(strategy, panels["indexation"])
    description = STRATEGY_DESCRIPTIONS.get(strategy, "")
    return (description, *styles)


@callback(
    Output("pf-cf-ts-accordion", "active_item"),
    Output("pf-cf-ts-accordion", "class_name"),
    Input("pf-cf-strategy-type", "value"),
    prevent_initial_call=True,
)
def open_ts_accordion_for_time_series(strategy):
    """Force-open the accordion in plain-block mode when switching to
    time_series (the block IS that strategy's only input); collapse it and
    restore the accordion chrome for any other strategy."""
    if strategy == "time_series":
        return "custom-cashflows", _ts_accordion_class(strategy)
    return None, _ts_accordion_class(strategy)


@callback(
    Output("pf-cf-frequency", "value"),
    Output("pf-cf-frequency", "disabled"),
    Output("pf-cf-frequency-row", "style"),
    Input("pf-cf-strategy-type", "value"),
    State("pf-cf-frequency", "value"),
)
def lock_frequency_for_strategy(strategy, current_freq):
    if strategy == "vds":
        return "year", True, None
    if strategy == "time_series":
        return "none", True, {"display": "none"}
    return current_freq, False, None


@callback(
    Output("pf-withdrawal-rate-col", "style"),
    Input("pf-cf-strategy-type", "value"),
)
def toggle_withdrawal_rate(strategy):
    if strategy in ("indexation", "cwd"):
        return None
    return {"display": "none"}


# --- TimeSeries dynamic rows ---


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
                dbc.Input(
                    id={"type": "pf-cf-ts-amount", "index": index},
                    type="number",
                    placeholder="-1000",
                    value=amount_val,
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


@callback(
    Output("pf-cf-ts-container", "children"),
    Input("pf-cf-ts-add", "n_clicks"),
    Input({"type": "pf-cf-ts-remove", "index": ALL}, "n_clicks"),
    Input("pf-cf-ts-accordion", "active_item"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "id"),
    State({"type": "pf-cf-ts-date", "index": ALL}, "value"),
    State({"type": "pf-cf-ts-amount", "index": ALL}, "value"),
    State("pf-cf-strategy-type", "value"),
)
def manage_ts_rows(add_clicks, remove_clicks, active_item, ids, dates, amounts, strategy):
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
    # accordion is collapsed the container stays empty.
    if not rows and active_item == "custom-cashflows":
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


# --- CWD dynamic rows ---


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

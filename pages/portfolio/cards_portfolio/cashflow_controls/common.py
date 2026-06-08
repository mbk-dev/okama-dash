"""Shared top section of the Cash Flow card (strategy selector, common amount /
discount-rate / frequency rows, Indexation panel) plus the cross-cutting
callbacks keyed on the strategy selector.

The visibility callbacks address panels in the feature modules
(``indexation``/``vds``/``cwd``/``find``) by their string ids, so no imports of
those modules are needed here.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State

from common import settings as settings
from common.mantine import search_provider
from .constants import STRATEGY_OPTIONS, STRATEGY_DESCRIPTIONS, FREQUENCY_OPTIONS
from .helpers import _prefill_amount
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def _strategy_selector(cf_strategy=None):
    return dbc.Row(
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
    )


def _common_amount_discount_row(initial_amount=None, discount_rate=None):
    return dbc.Row(
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
    )


def _frequency_row(cf_freq=None, cf_pct=None):
    return dbc.Row(
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
    )


def _indexation_panel(cashflow=None, cf_amount=None, cf_indexation=None):
    return html.Div(
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
    )


# --- Callbacks ---


@callback(
    Output("pf-cf-strategy-description", "children"),
    Output("pf-cf-indexation-panel", "style"),
    Output("pf-cf-percentage-col", "style"),
    Output("pf-cf-vds-panel", "style"),
    Output("pf-cf-cwd-panel", "style"),
    Output("pf-cf-find-block", "style"),
    Input("pf-cf-strategy-type", "value"),
)
def toggle_strategy_panels(strategy):
    show = None
    hide = {"display": "none"}
    # (indexation, percentage, vds, cwd, find_block) — the Find block is hidden
    # only for time_series (the okama solver doesn't accept TimeSeriesStrategy).
    panels = {
        "indexation": (show, hide, hide, hide, show),
        "percentage": (hide, show, hide, hide, show),
        "time_series": (hide, hide, hide, hide, hide),
        "vds": (hide, hide, show, hide, show),
        "cwd": (hide, hide, hide, show, show),
    }
    styles = panels.get(strategy, panels["indexation"])
    description = STRATEGY_DESCRIPTIONS.get(strategy, "")
    return (description, *styles)


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

"""Vanguard Dynamic Spending (VDS) strategy panel — layout only.

Visibility is driven by the shared ``toggle_strategy_panels`` callback
(``common.py``) via the ``pf-cf-vds-panel`` id, so this module has no callbacks.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from common.mantine import search_provider
from .helpers import _prefill_amount
import pages.portfolio.cards_portfolio.eng.pf_tooltips_options_txt as tl


def _vds_panel(
    vds_pct=None,
    vds_min=None,
    vds_max=None,
    vds_adj_mm=None,
    vds_floor=None,
    vds_ceil=None,
    vds_adj_fc=None,
    vds_indexation=None,
):
    return html.Div(
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
                            search_provider(
                                dmc.NumberInput(
                                    id="pf-cf-vds-min-withdrawal",
                                    min=0,
                                    value=_prefill_amount(vds_min, None),
                                    thousandSeparator=" ",
                                    placeholder="40 000",
                                )
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
                            search_provider(
                                dmc.NumberInput(
                                    id="pf-cf-vds-max-withdrawal",
                                    min=0,
                                    value=_prefill_amount(vds_max, None),
                                    thousandSeparator=" ",
                                    placeholder="100 000",
                                )
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
    )

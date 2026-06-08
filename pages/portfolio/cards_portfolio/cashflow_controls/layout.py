"""Assembles the Cash Flow Strategy accordion item from the per-feature panel
builders. Each section's layout, dynamic rows and callbacks live in its own
module (common / vds / cwd / find / timeseries)."""

import dash_bootstrap_components as dbc

from .common import (
    _strategy_selector,
    _common_amount_discount_row,
    _frequency_row,
    _indexation_panel,
)
from .vds import _vds_panel
from .cwd import _cwd_panel
from .find import _find_block
from .timeseries import _custom_cashflows_block


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
    return dbc.AccordionItem(
        [
            _strategy_selector(cf_strategy),
            _common_amount_discount_row(initial_amount, discount_rate),
            _frequency_row(cf_freq, cf_pct),
            _indexation_panel(cashflow, cf_amount, cf_indexation),
            _vds_panel(
                vds_pct,
                vds_min,
                vds_max,
                vds_adj_mm,
                vds_floor,
                vds_ceil,
                vds_adj_fc,
                vds_indexation,
            ),
            _cwd_panel(cwd_amount, cwd_indexation, cwd_tr),
            _find_block(),
            _custom_cashflows_block(cf_strategy, cf_ts),
        ],
        title="Cash Flow Strategy",
        item_id="cashflow",
    )

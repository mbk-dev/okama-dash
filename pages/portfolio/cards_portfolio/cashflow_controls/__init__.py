"""Cash Flow Strategy card — layout and callbacks, split by feature.

The public API is re-exported here so existing imports
``from pages.portfolio.cards_portfolio.cashflow_controls import <name>`` keep
working unchanged after the module was split into a package. Importing the
feature submodules also registers their Dash ``@callback``s (registration is
an import side effect) — ``layout`` pulls in every panel module.
"""

from .layout import cashflow_accordion_item
from .common import toggle_strategy_panels
from .timeseries import (
    _ts_collapse_is_open,
    _ts_body_class,
    set_ts_collapse_for_strategy,
    toggle_ts_collapse,
    manage_ts_rows,
)
from .cwd import should_disable_cwd_add, next_cwd_placeholder
from .find import (
    toggle_find_collapse,
    toggle_find_target_sp,
    validate_find_inputs,
    disable_find_button,
    reset_find_result,
)

__all__ = [
    "cashflow_accordion_item",
    "toggle_strategy_panels",
    "_ts_collapse_is_open",
    "_ts_body_class",
    "set_ts_collapse_for_strategy",
    "toggle_ts_collapse",
    "manage_ts_rows",
    "should_disable_cwd_add",
    "next_cwd_placeholder",
    "toggle_find_collapse",
    "toggle_find_target_sp",
    "validate_find_inputs",
    "disable_find_button",
    "reset_find_result",
]

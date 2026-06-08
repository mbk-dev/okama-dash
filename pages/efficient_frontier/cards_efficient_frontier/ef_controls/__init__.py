"""Efficient Frontier controls card — layout and callbacks, split by feature.

The public API is re-exported here so existing imports
``from pages.efficient_frontier.cards_efficient_frontier.ef_controls import <name>``
(production + tests) keep working unchanged. Importing each feature submodule
registers its Dash ``@callback``s: ``layout`` pulls in symbols/options via the
section builders, while ``links`` and ``gating`` are reached only through the
re-exports below.
"""

from .layout import card_controls
from .options import (
    toggle_simulation_inputs,
    update_grid_step_options,
    sync_incompatible_options,
)
from .links import update_link_ef
from .gating import disable_submit

__all__ = [
    "card_controls",
    "toggle_simulation_inputs",
    "update_grid_step_options",
    "sync_incompatible_options",
    "update_link_ef",
    "disable_submit",
]

"""Portfolio controls card — layout and callbacks, split by feature.

The public API is re-exported here so existing imports
``from pages.portfolio.cards_portfolio.portfolio_controls import <name>``
(production + tests) keep working unchanged. Importing each feature submodule
registers its Dash ``@callback``s (registration is an import side effect):
``layout`` pulls in constructor/options/monte_carlo via the section builders,
while ``links`` and ``gating`` are reached only through the re-exports below.
"""

from .layout import card_controls
from .constructor import validate_weight_input, print_weights_sum
from .options import disable_rolling_input
from .monte_carlo import (
    hide_monte_carlo_rows,
    show_hide_param_groups,
    toggle_mc_params_collapse,
    validate_df,
    check_validity_monte_carlo,
)
from .links import update_go_to_links
from .gating import disable_submit_add_link_buttons

__all__ = [
    "card_controls",
    "validate_weight_input",
    "print_weights_sum",
    "disable_rolling_input",
    "hide_monte_carlo_rows",
    "show_hide_param_groups",
    "toggle_mc_params_collapse",
    "validate_df",
    "check_validity_monte_carlo",
    "update_go_to_links",
    "disable_submit_add_link_buttons",
]

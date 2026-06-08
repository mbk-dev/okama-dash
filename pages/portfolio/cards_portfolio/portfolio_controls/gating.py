"""Button-gating callbacks: enable/disable Submit, Add Asset, Copy Link and the
'Go to' menu from the portfolio's validity, and the live withdrawal-rate readout."""

from typing import Tuple

import numpy as np
from dash import callback, ALL
from dash.dependencies import Input, Output

from common import settings as settings
import common.validators as validators


@callback(
    Output("pf-withdrawal-rate", "value"),
    Input("pf-initial-amount", "value"),
    Input("pf-cf-amount", "value"),
    Input("pf-cf-cwd-amount", "value"),
    Input("pf-cf-strategy-type", "value"),
    Input("pf-cf-frequency", "value"),
)
def print_withdrawal_rate(initial_amount, cf_amount, cwd_amount, strategy, frequency) -> str:
    freq_multiplier = {"month": 12, "quarter": 4, "half-year": 2, "year": 1}
    amount = cwd_amount if strategy == "cwd" else cf_amount
    if initial_amount and amount:
        periods_per_year = freq_multiplier.get(frequency, 12)
        withdrawal_rate = abs(float(amount)) * periods_per_year / float(initial_amount) * 100
    else:
        withdrawal_rate = 0
    return f"{withdrawal_rate:.0f}%"


@callback(
    Output("pf-submit-button", "disabled"),
    Output("pf-copy-link-button", "disabled"),
    Output("dynamic-add-filter", "disabled"),
    Output("pf-goto-menu", "disabled"),
    Input({"type": "pf-dynamic-dropdown", "index": ALL}, "value"),
    Input({"type": "pf-dynamic-input", "index": ALL}, "value"),
    Input("pf-rolling-window", "value"),
    Input("pf-monte-carlo-number", "valid"),
    Input("pf-monte-carlo-years", "valid"),
)
def disable_submit_add_link_buttons(
    tickers_list, weights_list, rolling_window_value, mc_number_valid, mc_years_valid
) -> Tuple[bool, bool, bool, bool]:
    """
    Disable "Add Asset", "Submit", "Copy Link" buttons and the "Go to" menu.

    disable "Add Asset" conditions:
    - weights and assets forms are not empty (don't have None)
    - number of tickers is more or equal than allowed (in settings)

    disable "Submit" conditions:
    - sum of weights is not 100
    - number of weights is not equal to the number of assets
    - rolling window size is natural number
    - MC number and MC forecast years are valid (incl. the number × years budget)

    disable "Copy Link" conditions:
    - "Submit"
    - number of tickers is more than allowed (in settings)

    disable "Go to" menu conditions (one gate for all three items):
    - "Copy Link"
    - number of unique tickers is < 2 (a frontier needs at least two assets)
    """
    add_condition1 = None in tickers_list or None in weights_list
    add_condition2 = len(tickers_list) >= settings.ALLOWED_NUMBER_OF_TICKERS
    add_result = add_condition1 or add_condition2

    tickers_list = [i for i in tickers_list if i is not None]
    weights_list = [i for i in weights_list if i is not None]

    weights_sum = sum(float(x) for x in weights_list if x)
    weights_sum_is_not_100 = np.around(weights_sum, decimals=3) != 100.0
    # 150 + -50 sums to 100 but each weight must itself stay within 0-100
    weights_out_of_range = any(not 0 <= float(w) <= 100 for w in weights_list if w != "")

    weights_and_tickers_has_different_length = len(set(tickers_list)) != len(weights_list)
    rolling_not_natural = validators.validate_integer_bool(rolling_window_value)

    mc_number_is_incorrect = not mc_number_valid
    mc_years_is_incorrect = not mc_years_valid

    submit_result = (
        weights_sum_is_not_100
        or weights_out_of_range
        or weights_and_tickers_has_different_length
        or rolling_not_natural
        or mc_number_is_incorrect
        or mc_years_is_incorrect
    )

    link_condition = len(tickers_list) > settings.ALLOWED_NUMBER_OF_TICKERS
    link_result = submit_result or link_condition
    # EF needs at least two assets: a one-asset "frontier" is just a point.
    go_to_ef_result = bool(link_result or len(set(tickers_list)) < 2)
    return submit_result, link_result, add_result, go_to_ef_result

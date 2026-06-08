"""Button-gating callbacks for the Efficient Frontier card: disable Copy Link
and Submit from the ticker count and Monte Carlo validity."""

from dash import callback
from dash.dependencies import Input, Output

from common.create_link import check_if_list_empty_or_big


@callback(
    Output("ef-copy-link-button", "disabled"),
    Input("ef-symbols-list", "value"),
)
def disable_link_button(tickers_list) -> bool:
    """
    Disable "Copy Link" button.

    Conditions:
    - list of tickers length is < 2
    - number of tickers is more than allowed (in settings)
    """
    return check_if_list_empty_or_big(tickers_list) or len(tickers_list) < 2


@callback(
    Output("ef-submit-button-state", "disabled"),
    Input("ef-symbols-list", "value"),
    Input("monte-carlo-option", "valid"),
    Input("ef-sim-mode", "value"),
)
def disable_submit(tickers_list, mc_number_valid, sim_mode) -> bool:
    """
    Disable Submit button.

    Conditions:
    - number of tickers is < 2
    - Monte Carlo mode is selected and its point count is invalid
    """
    number_of_tickers_is_too_small = len(tickers_list) < 2
    mc_number_is_incorrect = sim_mode == "Monte Carlo" and mc_number_valid is False
    return number_of_tickers_is_too_small or mc_number_is_incorrect

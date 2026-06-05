import pytest
from unittest.mock import patch

import dash

pytestmark = pytest.mark.component


def test_toggle_simulation_inputs_visibility():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import toggle_simulation_inputs

    mc_style, grid_style = toggle_simulation_inputs("Grid")
    assert mc_style == {"display": "none"}
    assert grid_style == {}

    mc_style, grid_style = toggle_simulation_inputs("Monte Carlo")
    assert mc_style == {}
    assert grid_style == {"display": "none"}

    mc_style, grid_style = toggle_simulation_inputs("Off")
    assert mc_style == {"display": "none"}
    assert grid_style == {"display": "none"}


def test_update_grid_step_options_disables_oversized_steps():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import update_grid_step_options

    options = update_grid_step_options(["T" + str(i) for i in range(7)])  # 7 tickers
    by_value = {opt["value"]: opt for opt in options}
    assert by_value["Auto"]["disabled"] is False
    assert by_value["0.1"]["disabled"] is True    # 8008 > 5000
    assert by_value["0.2"]["disabled"] is False    # 462 <= 5000


def test_update_grid_step_options_handles_empty_list():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import update_grid_step_options

    options = update_grid_step_options([])
    assert options[0]["value"] == "Auto"


def test_grid_mode_disables_pairwise():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import sync_incompatible_options

    with patch.object(dash, "ctx") as mock_ctx:
        mock_ctx.triggered_id = "ef-sim-mode"
        result = sync_incompatible_options("Frontier", "Off", "Off", "Grid")

    plot_options = result[0]
    pairwise = next(opt for opt in plot_options if opt["value"] == "Pairwise")
    assert pairwise["disabled"] is True


def test_selecting_pairwise_resets_sim_mode():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import sync_incompatible_options

    with patch.object(dash, "ctx") as mock_ctx:
        mock_ctx.triggered_id = "ef-plot-options"
        result = sync_incompatible_options(["Frontier", "Pairwise"], "Off", "Off", "Grid")

    sim_mode_out = result[6]
    assert sim_mode_out == "Off"


def test_disable_submit_ignores_mc_validity_in_grid_mode():
    from pages.efficient_frontier.cards_efficient_frontier.ef_controls import disable_submit

    assert disable_submit(["A.US", "B.US"], False, "Grid") is False
    assert disable_submit(["A.US", "B.US"], False, "Monte Carlo") is True
    assert disable_submit(["A.US"], True, "Off") is True

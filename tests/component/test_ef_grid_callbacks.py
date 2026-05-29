import pytest

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

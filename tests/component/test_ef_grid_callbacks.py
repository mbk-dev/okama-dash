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

from math import comb

import pytest

from common.ef_grid import (
    AUTO_STEP,
    grid_step_options,
    parse_grid_step_value,
    predicted_grid_points,
    resolve_grid_step,
)

pytestmark = pytest.mark.unit


def test_predicted_grid_points_matches_compositions_formula():
    assert predicted_grid_points(2, 0.1) == comb(11, 1) == 11
    assert predicted_grid_points(6, 0.1) == comb(15, 5) == 3003
    assert predicted_grid_points(7, 0.1) == comb(16, 6) == 8008
    assert predicted_grid_points(12, 0.2) == comb(16, 11) == 4368


def test_resolve_grid_step_uses_ten_percent_for_small_portfolios():
    assert resolve_grid_step(2) == 0.10
    assert resolve_grid_step(6) == 0.10


def test_resolve_grid_step_coarsens_when_ten_percent_exceeds_budget():
    # 7 assets @ 10% = 8008 > 5000, next finest allowed step is 20% (462)
    assert resolve_grid_step(7) == 0.20
    assert resolve_grid_step(12) == 0.20


def test_grid_step_options_disables_oversized_steps():
    options = grid_step_options(7)
    by_value = {opt["value"]: opt for opt in options}
    assert by_value[AUTO_STEP]["disabled"] is False
    assert by_value["0.1"]["disabled"] is True  # 8008 > 5000
    assert by_value["0.2"]["disabled"] is False  # 462 <= 5000


def test_grid_step_options_all_enabled_for_two_assets():
    options = grid_step_options(2)
    assert all(opt["disabled"] is False for opt in options)


def test_parse_grid_step_value_auto_resolves_by_asset_count():
    assert parse_grid_step_value(AUTO_STEP, 6) == 0.10
    assert parse_grid_step_value(AUTO_STEP, 7) == 0.20


def test_parse_grid_step_value_explicit_step_passes_through():
    assert parse_grid_step_value("0.25", 7) == 0.25

"""
Component tests: column sorting is disabled in every AG Grid table.

The widgets' tables are informational; clicking a header must not reorder
rows. AG Grid columns are sortable by default, so every grid has to opt out
via defaultColDef. These tests assert the wiring on each grid builder
(client-side behavior itself is out of reach — see "Known gaps" in AGENTS.md).
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

import dash_ag_grid as dag

from tests.mocks.okama_mock import (
    PicklableAssetList,
    make_mock_asset_list,
    make_mock_portfolio,
)

pytestmark = pytest.mark.component


def _find_grids(component) -> list:
    """Recursively collect dag.AgGrid instances from a Dash component tree."""
    grids = []
    if isinstance(component, dag.AgGrid):
        grids.append(component)
    children = getattr(component, "children", None)
    if children is None:
        return grids
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        grids.extend(_find_grids(child))
    return grids


def _assert_sorting_disabled(grids: list, expected_count: int):
    assert len(grids) == expected_count
    for grid in grids:
        assert grid.defaultColDef.get("sortable") is False


def test_db_namespaces_table_sorting_disabled():
    from pages.database.cards_database.db_namespaces import db_namespaces_table

    _assert_sorting_disabled([db_namespaces_table], expected_count=1)


def test_db_search_results_sorting_disabled(mock_okama_symbols, null_cache):
    from pages.database.cards_database.db_search_results import db_search

    grid = db_search(1, "Apple", "US")
    _assert_sorting_disabled([grid], expected_count=1)


def test_assets_names_and_info_grids_sorting_disabled():
    from common.html_elements.info_ag_grid import get_assets_names, get_info

    al_object = PicklableAssetList(["AAPL.US", "MSFT.US"])
    _assert_sorting_disabled([get_assets_names(al_object), get_info(al_object)], expected_count=2)


def test_compare_statistics_grid_sorting_disabled():
    from pages.compare.compare import get_al_statistics_table

    grid = get_al_statistics_table(make_mock_asset_list())
    _assert_sorting_disabled([grid], expected_count=1)


def test_pf_statistics_grid_sorting_disabled():
    from pages.portfolio.portfolio import get_pf_statistics_table

    grid = get_pf_statistics_table(make_mock_portfolio())
    _assert_sorting_disabled([grid], expected_count=1)


# scipy's lognorm.fit explores invalid loc values internally on sign-mixed
# returns; the RuntimeWarning is benign and data-dependent.
@pytest.mark.filterwarnings("ignore:invalid value encountered in log:RuntimeWarning")
def test_distribution_ks_grid_sorting_disabled():
    from pages.portfolio.portfolio import get_statistics_for_distribution

    statistics_html = get_statistics_for_distribution(make_mock_portfolio())
    _assert_sorting_disabled(_find_grids(statistics_html), expected_count=1)


def _pf_with_mc_stats():
    pf = make_mock_portfolio()
    pf.dcf.monte_carlo_survival_period.return_value = pd.Series([20.0, 25.0, 30.0])
    wealth_fv = pd.DataFrame({0: [100.0, 200.0], 1: [150.0, 250.0]})
    wealth_pv = wealth_fv / 2
    pf.dcf.monte_carlo_wealth = MagicMock(
        side_effect=lambda discounting="fv": wealth_fv if discounting == "fv" else wealth_pv
    )
    return pf


def test_survival_statistics_grids_sorting_disabled():
    from pages.portfolio.portfolio import get_forecast_survival_statistics_table

    pf = _pf_with_mc_stats()
    desktop = get_forecast_survival_statistics_table(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf)
    compact = get_forecast_survival_statistics_table(pd.DataFrame({"x": [1]}), pd.DataFrame(), pf, compact=True)
    _assert_sorting_disabled(_find_grids(desktop) + _find_grids(compact), expected_count=2)


def test_wealth_statistics_grids_sorting_disabled():
    from pages.portfolio.portfolio import get_forecast_wealth_statistics_table

    pf = _pf_with_mc_stats()
    desktop = get_forecast_wealth_statistics_table(pf)
    compact = get_forecast_wealth_statistics_table(pf, compact=True)
    _assert_sorting_disabled(_find_grids(desktop) + _find_grids(compact), expected_count=2)

"""Info panels must degrade gracefully when okama rejects a ticker.

All four pages share the same names/info panel pattern; an unknown or
malformed ticker arriving from a shareable link made ok.AssetList raise
(requests HTTPError 404 for delisted symbols like ``*.PIF``, ValueError for
a ticker without a namespace) and the callback 500ed (prod 2026-06-11).
"""

from unittest.mock import patch

import pytest
import requests

from common.html_elements.info_ag_grid import INFO_UNAVAILABLE_TEXT

pytestmark = pytest.mark.component

ERRORS = [
    requests.exceptions.HTTPError("0295-74549871.PIF is not found in the database.", 404),
    ValueError("RUGBITR5 is not in allowed assets namespaces: [...]"),
]


def _texts(component) -> str:
    return str(component)


@pytest.mark.parametrize("error", ERRORS, ids=["http-404", "value-error"])
class TestInfoPanelsSurviveBadTickers:
    def test_compare_info_panel(self, error, mock_okama_symbols, null_cache):
        from pages.compare.cards_compare import assets_info

        with patch("pages.compare.cards_compare.assets_info.ok.AssetList", side_effect=error):
            names, info = assets_info.pf_update_asset_names_info(["BAD.PIF"], "USD", False, None)

        assert INFO_UNAVAILABLE_TEXT in _texts(names)
        assert INFO_UNAVAILABLE_TEXT in _texts(info)

    def test_benchmark_info_panel(self, error, mock_okama_symbols, null_cache):
        from pages.benchmark.cards_benchmark import benchmark_info

        with patch("pages.benchmark.cards_benchmark.benchmark_info.ok.AssetList", side_effect=error):
            names, info = benchmark_info.pf_update_asset_names_info(["BAD.PIF"], "RUGBITR5", "RUB", None)

        assert INFO_UNAVAILABLE_TEXT in _texts(names)
        assert INFO_UNAVAILABLE_TEXT in _texts(info)

    def test_portfolio_info_panel(self, error, mock_okama_symbols, null_cache):
        from pages.portfolio.cards_portfolio import portfolio_info

        with patch("pages.portfolio.cards_portfolio.portfolio_info.ok.AssetList", side_effect=error):
            names, info = portfolio_info.pf_update_asset_names_info(["BAD.PIF"], "USD", False)

        assert INFO_UNAVAILABLE_TEXT in _texts(names)
        assert INFO_UNAVAILABLE_TEXT in _texts(info)

    def test_ef_info_panel(self, error, mock_okama_symbols, null_cache):
        from pages.efficient_frontier.cards_efficient_frontier import ef_info

        with patch(
            "pages.efficient_frontier.cards_efficient_frontier.ef_info.ok.AssetList", side_effect=error
        ):
            names, info = ef_info.pf_update_asset_names_info(["BAD.PIF"], "USD")

        assert INFO_UNAVAILABLE_TEXT in _texts(names)
        assert INFO_UNAVAILABLE_TEXT in _texts(info)

"""EF info panel must take its okama settings from the same source as the frontier.

The frontier (ef_cache) is built with one inflation setting and the page
currency (ef-base-currency). The "Information" panel used to hardcode its own
inflation and ignore the currency, so the two could drift — and did: it built a
bare ``ok.AssetList(assets)`` (okama default inflation=True) and reported a "Last
available date" a month behind the frontier (the inflation series publishes ~1
month late). The panel now reads inflation from ``ef_cache.EF_INFLATION`` and the
currency from the same ``ef-base-currency`` control the frontier uses, so the two
share a single source of truth and cannot drift.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.component


def _capture_assetlist_kwargs(assets, ccy):
    """Run the EF info callback and return the kwargs ok.AssetList was built with."""
    from pages.efficient_frontier.cards_efficient_frontier import ef_info

    captured = {}

    def capture(al_factory):
        captured["factory"] = al_factory
        return ("names", "info")

    with patch.object(ef_info, "names_and_info_tables", side_effect=capture):
        ef_info.pf_update_asset_names_info(assets, ccy)

    with patch.object(ef_info.ok, "AssetList") as mock_al:
        captured["factory"]()
    return mock_al.call_args.kwargs


def test_ef_info_inflation_comes_from_shared_ef_source():
    from pages.efficient_frontier import ef_cache

    kwargs = _capture_assetlist_kwargs(["AAPL.US", "MSFT.US"], "USD")
    assert kwargs.get("inflation") == ef_cache.EF_INFLATION


def test_ef_info_uses_page_currency():
    kwargs = _capture_assetlist_kwargs(["AAPL.US", "MSFT.US"], "RUB")
    assert kwargs.get("ccy") == "RUB"

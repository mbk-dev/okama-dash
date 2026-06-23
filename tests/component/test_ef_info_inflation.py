"""EF info panel must build its AssetList with inflation=False.

The Efficient Frontier itself is built with inflation=False, but the
"Information" panel was building a bare ``ok.AssetList(assets)`` — which uses
okama's default ``inflation=True``. The default-currency inflation series
(e.g. USD.INFL) is published with a ~1-month delay, so inflation=True caps the
AssetList's ``last_date`` to the last published inflation month. The panel then
reported a "Last available date" one month behind the data the frontier is
actually computed on (live: info said 2026-05 while the frontier ran through
2026-06). Match the frontier (and the benchmark page's info panel), which use
inflation=False.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.component


def test_ef_info_builds_assetlist_without_inflation():
    from pages.efficient_frontier.cards_efficient_frontier import ef_info

    captured = {}

    def capture(al_factory):
        captured["factory"] = al_factory
        return ("names", "info")

    with patch.object(ef_info, "names_and_info_tables", side_effect=capture):
        ef_info.pf_update_asset_names_info(["AAPL.US", "MSFT.US"])

    with patch.object(ef_info.ok, "AssetList") as mock_al:
        captured["factory"]()

    assert mock_al.call_args.kwargs.get("inflation") is False, (
        "EF info-table AssetList must be built with inflation=False to match the "
        "frontier; inflation=True caps 'Last available date' to the inflation "
        "publication month, a month behind the asset data."
    )

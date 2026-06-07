"""Wiring tests for the cached macro-object accessors.

Each accessor must route through common.object_cache.get_or_create with a
distinct obj_type, pass the page's date bounds into the okama constructor,
and use the shared asset-list TTL.
"""

from unittest.mock import MagicMock, patch

import pytest

from common.object_cache import TTL_ASSET_LIST
from pages.macro import macro_objects

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("accessor", "obj_type", "okama_cls", "symbol"),
    [
        (macro_objects.get_inflation_object, "inflation", "Inflation", "RUB.INFL"),
        (macro_objects.get_rate_object, "rate", "Rate", "RUS_CBR.RATE"),
        (macro_objects.get_indicator_object, "indicator", "Indicator", "USA_CAPE10.RATIO"),
    ],
)
def test_accessor_wires_cache_and_constructor(accessor, obj_type, okama_cls, symbol):
    sentinel = MagicMock()
    with (
        patch.object(macro_objects, "get_or_create") as goc,
        patch.object(macro_objects.ok, okama_cls, return_value=sentinel) as cls_mock,
    ):
        goc.side_effect = lambda **kwargs: (kwargs["constructor_fn"](), "key.pkl")

        result = accessor(symbol, "2000-01", "2026-05")

        assert result is sentinel
        cls_mock.assert_called_once_with(symbol, first_date="2000-01", last_date="2026-05")
        kwargs = goc.call_args.kwargs
        assert kwargs["obj_type"] == obj_type
        assert kwargs["cache_key_params"] == {
            "symbols": [symbol],
            "first_date": "2000-01",
            "last_date": "2026-05",
        }
        assert kwargs["ttl_seconds"] == TTL_ASSET_LIST


def test_asset_accessor_wires_cache_and_constructor():
    sentinel = MagicMock()
    with (
        patch.object(macro_objects, "get_or_create") as goc,
        patch.object(macro_objects.ok, "Asset", return_value=sentinel) as cls_mock,
    ):
        goc.side_effect = lambda **kwargs: (kwargs["constructor_fn"](), "key.pkl")
        result = macro_objects.get_asset_object("MOW_PR.RE")
        assert result is sentinel
        cls_mock.assert_called_once_with("MOW_PR.RE")
        kwargs = goc.call_args.kwargs
        assert kwargs["obj_type"] == "asset"
        assert kwargs["cache_key_params"] == {"symbols": ["MOW_PR.RE"]}
        assert kwargs["ttl_seconds"] == TTL_ASSET_LIST


def test_asset_list_accessor_wires_cache_and_constructor():
    sentinel = MagicMock()
    with (
        patch.object(macro_objects, "get_or_create") as goc,
        patch.object(macro_objects.ok, "AssetList", return_value=sentinel) as cls_mock,
    ):
        goc.side_effect = lambda **kwargs: (kwargs["constructor_fn"](), "key.pkl")
        result = macro_objects.get_asset_list_object(
            ["MOW_PR.RE", "MOW_SEC.RE"], ccy="USD", first_date="2000-04", last_date="2026-03", inflation=True
        )
        assert result is sentinel
        cls_mock.assert_called_once_with(
            ["MOW_PR.RE", "MOW_SEC.RE"], ccy="USD", first_date="2000-04", last_date="2026-03", inflation=True
        )
        kwargs = goc.call_args.kwargs
        assert kwargs["obj_type"] == "assetlist"
        assert kwargs["cache_key_params"] == {
            "symbols": ["MOW_PR.RE", "MOW_SEC.RE"],
            "ccy": "USD",
            "first_date": "2000-04",
            "last_date": "2026-03",
            "inflation": True,
        }
        assert kwargs["ttl_seconds"] == TTL_ASSET_LIST


def test_private_price_converter_still_exists_in_okama():
    # The RE page calls AssetList._adjust_price_to_currency_monthly (okama has
    # no public converted-price API — verified 2026-06-07). This guard fails on
    # an okama upgrade that removes/renames it, pointing straight at the spot.
    import inspect

    method = getattr(macro_objects.ok.AssetList, "_adjust_price_to_currency_monthly", None)
    assert method is not None, "okama dropped _adjust_price_to_currency_monthly — rework the RE USD price path"
    params = list(inspect.signature(method).parameters)
    assert params[1:3] == ["price", "asset_currency"]

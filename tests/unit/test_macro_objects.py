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

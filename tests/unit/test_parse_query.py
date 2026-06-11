"""URL query parsing must survive malformed values: a broken shareable link
should degrade to defaults, not crash the page layout (prod 2026-06-11:
?weights=34.33.33 produced a 500 for the whole /portfolio page)."""

import pytest

from common.parse_query import make_list_from_string

pytestmark = pytest.mark.unit


class TestMakeListFromString:
    def test_str_list(self):
        assert make_list_from_string("AAPL.US,MSFT.US") == ["AAPL.US", "MSFT.US"]

    def test_float_list(self):
        assert make_list_from_string("10,20,70", char_type="float") == [10.0, 20.0, 70.0]

    def test_none_returns_none(self):
        assert make_list_from_string(None) is None

    def test_empty_string_returns_none(self):
        assert make_list_from_string("") is None

    def test_malformed_float_returns_none(self):
        # A typo'd weights param ("34.33.33" instead of "34,33,33") must fall
        # back to None (defaults) instead of raising out of the page layout.
        assert make_list_from_string("34.33.33", char_type="float") is None

    def test_partially_malformed_float_returns_none(self):
        assert make_list_from_string("10,abc,70", char_type="float") is None

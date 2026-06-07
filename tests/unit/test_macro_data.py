"""Integrity tests for the curated macro-series catalog.

The catalog is the single source of truth for which okama DB series the Macro
pages expose. Symbols were verified against the live okama database
(spec 2026-06-07-macro-section-design.md §2) — these tests guard the
*structure*, not the DB itself.
"""

import pytest

from pages.macro.macro_data import (
    CAPE10_DEFAULTS,
    CAPE10_SERIES,
    INFLATION_DEFAULTS,
    INFLATION_SERIES,
    INFLATION_TO_KEY_RATE,
    KEY_RATES_SERIES,
    MACRO_FIRST_DATE_DEFAULT,
    RATES_DEFAULTS,
    filter_known,
)

pytestmark = pytest.mark.unit


class TestCatalogIntegrity:
    def test_inflation_series_use_infl_namespace(self):
        assert len(INFLATION_SERIES) == 6
        assert all(s.endswith(".INFL") for s in INFLATION_SERIES)

    def test_key_rates_use_rate_namespace(self):
        assert len(KEY_RATES_SERIES) == 9
        assert all(s.endswith(".RATE") for s in KEY_RATES_SERIES)

    def test_cape10_has_26_ratio_countries(self):
        assert len(CAPE10_SERIES) == 26
        assert all(s.endswith("_CAPE10.RATIO") for s in CAPE10_SERIES)

    def test_overlay_mapping_covers_every_inflation_currency(self):
        assert set(INFLATION_TO_KEY_RATE) == set(INFLATION_SERIES)
        assert all(rate in KEY_RATES_SERIES for rate in INFLATION_TO_KEY_RATE.values())

    def test_ecb_overlay_rate_is_mro(self):
        # User decision in the spec (§5.1): MRO, not DFR.
        assert INFLATION_TO_KEY_RATE["EUR.INFL"] == "EU_MRO.RATE"

    def test_defaults_are_members_of_their_catalogs(self):
        assert INFLATION_DEFAULTS and set(INFLATION_DEFAULTS) <= set(INFLATION_SERIES)
        assert RATES_DEFAULTS and set(RATES_DEFAULTS) <= set(KEY_RATES_SERIES)
        assert CAPE10_DEFAULTS and set(CAPE10_DEFAULTS) <= set(CAPE10_SERIES)

    def test_default_first_date(self):
        assert MACRO_FIRST_DATE_DEFAULT == "2000-01"


class TestFilterKnown:
    def test_drops_symbols_missing_from_catalog(self):
        assert filter_known(["RUB.INFL", "FAKE.INFL"], INFLATION_SERIES) == ["RUB.INFL"]

    def test_none_and_empty_return_empty_list(self):
        assert filter_known(None, INFLATION_SERIES) == []
        assert filter_known([], INFLATION_SERIES) == []

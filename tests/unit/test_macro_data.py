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
    DEPOSIT_RATES_SERIES,
    INFLATION_DEFAULTS,
    INFLATION_SERIES,
    INFLATION_TO_KEY_RATE,
    KEY_RATES_SERIES,
    MACRO_FIRST_DATE_DEFAULT,
    MONEY_MARKET_SERIES,
    RATES_DEFAULTS,
    RATES_GROUPS,
    RE_DEFAULTS,
    RE_SERIES,
    filter_known,
    rates_group_catalog,
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


class TestRateGroups:
    def test_deposit_group_has_4_rate_series(self):
        assert len(DEPOSIT_RATES_SERIES) == 4
        assert all(s.endswith(".RATE") for s in DEPOSIT_RATES_SERIES)

    def test_money_market_group_has_9_rate_series(self):
        assert len(MONEY_MARKET_SERIES) == 9
        assert all(s.endswith(".RATE") for s in MONEY_MARKET_SERIES)

    def test_groups_registry_wires_label_catalog_defaults(self):
        assert set(RATES_GROUPS) == {"key", "deposit", "mm"}
        for label, catalog, defaults in RATES_GROUPS.values():
            assert isinstance(label, str) and label
            assert defaults and set(defaults) <= set(catalog)

    def test_key_group_reuses_stage1_catalog(self):
        assert RATES_GROUPS["key"][1] is KEY_RATES_SERIES
        assert RATES_GROUPS["key"][2] == RATES_DEFAULTS

    def test_groups_do_not_overlap(self):
        keys = set(KEY_RATES_SERIES)
        assert not keys & set(DEPOSIT_RATES_SERIES)
        assert not set(DEPOSIT_RATES_SERIES) & set(MONEY_MARKET_SERIES)
        assert not keys & set(MONEY_MARKET_SERIES)

    def test_rates_group_catalog_resolves_and_falls_back(self):
        assert rates_group_catalog("deposit") is DEPOSIT_RATES_SERIES
        assert rates_group_catalog("unknown") is KEY_RATES_SERIES  # safe default
        assert rates_group_catalog(None) is KEY_RATES_SERIES


class TestRealEstateCatalog:
    def test_re_series_use_re_namespace(self):
        assert len(RE_SERIES) == 4
        assert all(s.endswith(".RE") for s in RE_SERIES)

    def test_re_defaults_are_moscow_pair(self):
        assert RE_DEFAULTS == ["MOW_PR.RE", "MOW_SEC.RE"]
        assert set(RE_DEFAULTS) <= set(RE_SERIES)

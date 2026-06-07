"""Tests for the macro describe()-table builders.

okama macro classes are single-symbol: a multi-series stats table is built by
outer-merging per-symbol describe() frames on (property, period). Full-period
rows may carry symbol-specific period strings (e.g. '26 years' vs '12 years,
9 months' when histories differ) — the merge must keep both rows rather than
mis-align values.
"""

import pandas as pd
import pytest

from pages.macro.cards_macro.macro_stats import build_describe_table, build_stats_grid

pytestmark = pytest.mark.unit


def _describe(symbol: str, periods: list[str], values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"property": ["arithmetic mean"] * len(periods), "period": periods, symbol: values}
    )


class TestBuildDescribeTable:
    def test_aligned_periods_merge_into_single_rows(self):
        a = _describe("A.RATE", ["YTD", "1 years"], [0.1, 0.2])
        b = _describe("B.RATE", ["YTD", "1 years"], [0.3, 0.4])
        merged = build_describe_table([a, b])
        assert list(merged.columns) == ["property", "period", "A.RATE", "B.RATE"]
        assert len(merged) == 2
        assert merged.loc[merged["period"] == "YTD", "B.RATE"].iloc[0] == 0.3

    def test_mismatched_full_period_rows_are_kept_separately(self):
        a = _describe("A.RATE", ["YTD", "26 years"], [0.1, 0.2])
        b = _describe("B.RATE", ["YTD", "12 years"], [0.3, 0.4])
        merged = build_describe_table([a, b])
        assert len(merged) == 3  # YTD shared + one full-period row per symbol
        full_a = merged.loc[merged["period"] == "26 years", "B.RATE"]
        assert full_a.isna().all()

    def test_single_series_passes_through(self):
        a = _describe("A.RATE", ["YTD"], [0.1])
        merged = build_describe_table([a])
        pd.testing.assert_frame_equal(merged, a)


class TestBuildStatsGrid:
    def test_percent_formatter_on_value_columns_only(self):
        df = _describe("RUS_CBR.RATE", ["YTD"], [0.15])
        grid = build_stats_grid(df, "rates-describe-table-grid", value_format="percent")
        defs = {d["field"]: d for d in grid.columnDefs}
        assert "valueFormatter" not in defs["property"]
        assert "valueFormatter" not in defs["period"]
        assert defs["RUS_CBR.RATE"]["valueFormatter"]["function"] == "formatPercentGuarded(params.value)"

    def test_decimal_formatter_for_cape(self):
        df = _describe("USA_CAPE10.RATIO", ["YTD"], [38.7])
        grid = build_stats_grid(df, "cape-describe-table-grid", value_format="decimal")
        defs = {d["field"]: d for d in grid.columnDefs}
        assert defs["USA_CAPE10.RATIO"]["valueFormatter"]["function"] == "formatDecimalGuarded(params.value)"

    def test_grid_conventions(self):
        # AGENTS.md: informational grids — no sorting/resizing; dotted symbol
        # columns need suppressFieldDotNotation (AAPL.US precedent).
        df = _describe("A.RATE", ["YTD"], [0.1])
        grid = build_stats_grid(df, "x-grid", value_format="percent")
        assert grid.defaultColDef == {"resizable": False, "sortable": False}
        assert grid.dashGridOptions["suppressFieldDotNotation"] is True
        assert grid.rowData == df.to_dict("records")

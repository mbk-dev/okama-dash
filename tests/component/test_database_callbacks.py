from unittest.mock import patch

import dash_ag_grid as dag
import pandas as pd
import pytest

pytestmark = pytest.mark.component

SEARCH_MODULE = "pages.database.cards_database.db_search_results"


def _make_search_df(n_rows: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": [f"TICK{i}.US" for i in range(n_rows)],
            "ticker": [f"TICK{i}" for i in range(n_rows)],
            "name": [f"Company {i}" for i in range(n_rows)],
            "isin": [f"US000000000{i}" for i in range(n_rows)],
        }
    )


class TestDbSearch:
    def test_results_found_returns_datatable(self):
        from pages.database.cards_database.db_search_results import db_search

        with patch(f"{SEARCH_MODULE}.ok.search", return_value=_make_search_df(3)):
            result = db_search(1, "TICK", "US")

        assert isinstance(result, dag.AgGrid)
        assert len(result.rowData) == 3
        assert result.dashGridOptions["pagination"] is True
        assert result.dashGridOptions["paginationPageSize"] == 15

    def test_ticker_column_dropped_from_results(self):
        from pages.database.cards_database.db_search_results import db_search

        with patch(f"{SEARCH_MODULE}.ok.search", return_value=_make_search_df(2)):
            result = db_search(1, "TICK", "US")

        columns_in_data = set(result.rowData[0].keys())
        assert "ticker" not in columns_in_data
        assert "symbol" in columns_in_data
        assert "name" in columns_in_data

    def test_empty_result_any_namespace(self):
        from pages.database.cards_database.db_search_results import db_search

        empty_df = pd.DataFrame(columns=["symbol", "ticker", "name", "isin"])
        with patch(f"{SEARCH_MODULE}.ok.search", return_value=empty_df):
            result = db_search(1, "nonexistent", "ANY")

        assert result == "Not found in the database ..."

    def test_empty_result_specific_namespace(self):
        from pages.database.cards_database.db_search_results import db_search

        empty_df = pd.DataFrame(columns=["symbol", "ticker", "name", "isin"])
        with patch(f"{SEARCH_MODULE}.ok.search", return_value=empty_df):
            result = db_search(1, "nonexistent", "XETR")

        assert result == "Not found in XETR namespace ..."

    def test_any_namespace_passes_none_to_ok_search(self):
        from pages.database.cards_database.db_search_results import db_search

        with patch(f"{SEARCH_MODULE}.ok.search", return_value=_make_search_df(1)) as mock_search:
            db_search(1, "apple", "ANY")

        mock_search.assert_called_once_with("apple", namespace=None)

    def test_specific_namespace_passed_through(self):
        from pages.database.cards_database.db_search_results import db_search

        with patch(f"{SEARCH_MODULE}.ok.search", return_value=_make_search_df(1)) as mock_search:
            db_search(1, "apple", "US")

        mock_search.assert_called_once_with("apple", namespace="US")

    @pytest.mark.parametrize("blank", [None, "", "   "])
    def test_blank_query_is_not_searched(self, blank):
        # An untouched search box sends value=None; ok.search(None) → pandas
        # .str.contains(None) → re.compile(None) → TypeError (prod 500, 2026-06).
        # A blank query must short-circuit to a prompt, never reaching okama.
        from pages.database.cards_database.db_search_results import db_search

        with patch(f"{SEARCH_MODULE}.ok.search") as mock_search:
            result = db_search(1, blank, "ANY")

        mock_search.assert_not_called()
        assert isinstance(result, str)


class TestDatabaseLayout:
    def test_layout_tolerates_arbitrary_query_params(self, mock_okama_symbols, null_cache):
        # Dash passes URL query params as kwargs to layout(); campaign links
        # like /database?utm_source=... must not 500 the page (prod 2026-06-11).
        from pages.database.database import layout

        page = layout(utm_source="rostsber", utm_medium="email", utm_campaign="x")
        assert page is not None

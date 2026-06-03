import pytest

from common.symbols import (
    get_symbol_search_index,
    get_symbols,
    get_symbols_names,
    search_symbol_options,
    search_symbols,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _setup(mock_okama_symbols, null_cache):
    pass


class TestGetSymbols:
    def test_returns_list(self):
        result = get_symbols()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_known_symbols(self):
        result = get_symbols()
        assert "AAPL.US" in result
        assert "SP500TR.INDX" in result

    def test_contains_all_fixture_symbols(self):
        result = get_symbols()
        assert "MSFT.US" in result
        assert "GOOG.US" in result
        assert "MCFTR.INDX" in result


class TestGetSymbolsNames:
    def test_returns_list_of_dicts(self):
        result = get_symbols_names()
        assert isinstance(result, list)
        assert all("long_name" in item and "symbol" in item for item in result)

    def test_long_name_format(self):
        result = get_symbols_names()
        aapl = next(item for item in result if item["symbol"] == "AAPL.US")
        assert aapl["long_name"] == "AAPL.US : Apple Inc"


class TestGetSymbolSearchIndex:
    def test_returns_sorted_lists(self):
        index = get_symbol_search_index()
        assert "symbols" in index
        assert "normalized_symbols" in index
        assert len(index["symbols"]) == len(index["normalized_symbols"])
        assert index["normalized_symbols"] == sorted(index["normalized_symbols"])

    def test_no_duplicates(self):
        index = get_symbol_search_index()
        assert len(index["symbols"]) == len(set(index["symbols"]))


class TestSearchSymbols:
    def test_prefix_match(self):
        result = search_symbols("AAPL")
        assert "AAPL.US" in result

    def test_case_insensitive(self):
        result = search_symbols("aapl")
        assert "AAPL.US" in result

    def test_empty_query_returns_selected(self):
        result = search_symbols("", ["MSFT.US"])
        assert result == ["MSFT.US"]

    def test_none_query_returns_selected(self):
        result = search_symbols(None, ["MSFT.US"])
        assert result == ["MSFT.US"]

    def test_empty_query_no_selected_returns_empty(self):
        result = search_symbols("")
        assert result == []

    def test_nonexistent_ticker(self):
        result = search_symbols("ZZZZZ")
        assert result == []

    def test_selected_values_appended(self):
        result = search_symbols("AAPL", ["MSFT.US"])
        assert "AAPL.US" in result
        assert "MSFT.US" in result

    def test_namespace_prefix(self):
        result = search_symbols("SP500")
        assert any("SP500" in s for s in result)

    def test_partial_prefix(self):
        result = search_symbols("MS")
        assert "MSFT.US" in result


class TestSearchSymbolOptions:
    def test_returns_option_dicts(self):
        result = search_symbol_options("AAPL")
        assert isinstance(result, list)
        assert all("label" in opt and "value" in opt for opt in result)

    def test_prefix_match_by_ticker(self):
        result = search_symbol_options("MSFT")
        values = [opt["value"] for opt in result]
        assert "MSFT.US" in values

    def test_name_token_search(self):
        result = search_symbol_options("Apple")
        values = [opt["value"] for opt in result]
        assert "AAPL.US" in values

    def test_empty_query_returns_selected_only(self):
        result = search_symbol_options("", ["AAPL.US"])
        values = [opt["value"] for opt in result]
        assert values == ["AAPL.US"]

    def test_empty_query_no_selected_returns_empty(self):
        result = search_symbol_options("")
        assert result == []

    def test_selected_values_preserved(self):
        result = search_symbol_options("GOOG", ["AAPL.US"])
        values = [opt["value"] for opt in result]
        assert "GOOG.US" in values
        assert "AAPL.US" in values

    def test_case_insensitive_name_search(self):
        result = search_symbol_options("microsoft")
        values = [opt["value"] for opt in result]
        assert "MSFT.US" in values

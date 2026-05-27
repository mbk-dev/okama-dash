from bisect import bisect_left, bisect_right
import re
from typing import Optional

import pandas as pd
import okama as ok

from common import cache
import common.settings as settings

SEARCH_RESULTS_LIMIT = 100
NAME_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


@cache.memoize(timeout=2592000)
def get_symbols() -> list:
    """
    Get all available symbols (tickers) from assets namespaces.
    """
    list_of_symbols = [ok.symbols_in_namespace(ns).symbol for ns in settings.get_namespaces()]
    classifier_df = pd.concat(list_of_symbols, axis=0, join="outer", copy=False, ignore_index=True)
    return classifier_df.to_list()


def get_symbols_names() -> dict:
    """
    Get a dictionary of long_name + symbol values.
    """
    namespaces = ok.assets_namespaces
    list_of_symbols = [ok.symbols_in_namespace(ns).loc[:, ["symbol", "name"]] for ns in namespaces]
    classifier_df = pd.concat(list_of_symbols, axis=0, join="outer", copy=False, ignore_index=True)
    classifier_df["long_name"] = classifier_df.symbol + " : " + classifier_df.name
    return classifier_df.loc[:, ["long_name", "symbol"]].to_dict("records")


@cache.memoize(timeout=2592000)
def get_symbol_search_index() -> dict:
    """
    Prepare a sorted index for fast prefix lookup by ticker.
    """
    symbols = sorted(set(get_symbols()), key=str.casefold)
    normalized_symbols = [symbol.casefold() for symbol in symbols]
    return {"symbols": symbols, "normalized_symbols": normalized_symbols}


@cache.memoize(timeout=2592000)
def get_symbol_options_index() -> dict:
    """
    Prepare a sorted index for fast dropdown lookup by ticker and asset-name tokens.
    """
    symbol_rows = sorted(get_symbols_names(), key=lambda item: item["symbol"].casefold())
    options = [{"label": item["long_name"], "value": item["symbol"]} for item in symbol_rows]
    normalized_symbols = [item["symbol"].casefold() for item in symbol_rows]
    by_symbol = {option["value"]: option for option in options}

    name_token_pairs = []
    for row in symbol_rows:
        seen_tokens = set()
        name_part = row["long_name"].partition(" : ")[2]
        for token in NAME_TOKEN_PATTERN.findall(name_part.casefold()):
            if token in seen_tokens:
                continue
            name_token_pairs.append((token, row["symbol"]))
            seen_tokens.add(token)

    name_token_pairs.sort()
    name_tokens = [token for token, _ in name_token_pairs]
    name_token_symbols = [symbol for _, symbol in name_token_pairs]
    return {
        "options": options,
        "normalized_symbols": normalized_symbols,
        "name_tokens": name_tokens,
        "name_token_symbols": name_token_symbols,
        "by_symbol": by_symbol,
    }


def _prefix_bounds(sorted_values: list[str], prefix: str) -> tuple[int, int]:
    left = bisect_left(sorted_values, prefix)
    right = bisect_right(sorted_values, prefix + "\uffff")
    return left, right


def _normalize_search_value(search_value: Optional[str]) -> str:
    return (search_value or "").strip().casefold()


def _append_missing_values(values: list[str], selected_values: Optional[list[str]]) -> list[str]:
    result = list(values)
    seen = set(result)
    for value in selected_values or []:
        if value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _append_missing_options(matched_options: list[dict], selected_options: list[dict]) -> list[dict]:
    result = list(matched_options)
    seen_values = {option["value"] for option in result}
    for option in selected_options:
        if option["value"] in seen_values:
            continue
        result.append(option)
        seen_values.add(option["value"])
    return result


def _make_selected_option(value: str) -> dict:
    return {"label": value, "value": value}


def search_symbols(search_value: Optional[str], selected_values: Optional[list[str]] = None) -> list[str]:
    """
    Return up to SEARCH_RESULTS_LIMIT ticker matches by prefix.
    """
    normalized_search = _normalize_search_value(search_value)
    if not normalized_search:
        return selected_values or []

    search_index = get_symbol_search_index()
    left, right = _prefix_bounds(search_index["normalized_symbols"], normalized_search)
    matched_values = search_index["symbols"][left : min(right, left + SEARCH_RESULTS_LIMIT)]
    return _append_missing_values(matched_values, selected_values)


def get_selected_symbol_options(selected_values: Optional[list[str]]) -> list[dict]:
    """
    Return dropdown options for already selected tickers only.
    """
    if not selected_values:
        return []

    by_symbol = get_symbol_options_index()["by_symbol"]
    return [_make_selected_option(value) for value in selected_values if value in by_symbol]


def search_symbol_options(search_value: Optional[str], selected_values: Optional[list[str]] = None) -> list[dict]:
    """
    Return dropdown options for efficient frontier search.

    Prefix lookup by ticker is O(log n), and if there is free room in the response
    we additionally search by asset-name tokens to keep name-based search practical.
    """
    selected_options = get_selected_symbol_options(selected_values)
    selected_values_set = set(selected_values or [])
    normalized_search = _normalize_search_value(search_value)
    if not normalized_search:
        return selected_options

    search_index = get_symbol_options_index()
    left, right = _prefix_bounds(search_index["normalized_symbols"], normalized_search)
    matched_options = search_index["options"][left : min(right, left + SEARCH_RESULTS_LIMIT)]
    matched_options = [
        _make_selected_option(option["value"]) if option["value"] in selected_values_set else option
        for option in matched_options
    ]

    remaining_limit = SEARCH_RESULTS_LIMIT - len(matched_options)
    if remaining_limit > 0 and len(normalized_search) >= 2:
        token_left, token_right = _prefix_bounds(search_index["name_tokens"], normalized_search)
        matched_symbols = {option["value"] for option in matched_options}
        for symbol in search_index["name_token_symbols"][token_left:token_right]:
            if symbol in matched_symbols:
                continue
            option = _make_selected_option(symbol) if symbol in selected_values_set else search_index["by_symbol"][symbol]
            matched_options.append(option)
            matched_symbols.add(symbol)
            remaining_limit -= 1
            if remaining_limit == 0:
                break

    return _append_missing_options(matched_options, selected_options)

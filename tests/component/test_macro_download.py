"""Download-data callback helper for macro charts (benchmark pattern)."""

import dash
import pandas as pd
import pytest

from pages.macro.cards_macro.macro_download import download_from_store

pytestmark = pytest.mark.component


def test_download_prevents_update_without_clicks():
    json_data = pd.DataFrame({"a": [1, 2]}).to_json(orient="split")
    with pytest.raises(dash.exceptions.PreventUpdate):
        download_from_store(None, json_data)


def test_download_prevents_update_without_data():
    with pytest.raises(dash.exceptions.PreventUpdate):
        download_from_store(1, None)


def test_download_returns_xlsx_dict():
    json_data = pd.DataFrame({"a": [1, 2]}).to_json(orient="split")
    result = download_from_store(1, json_data)
    assert result["filename"].endswith(".xlsx")

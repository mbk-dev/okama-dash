"""
Component tests for grid xlsx export helper.
"""

import pytest
import dash_bootstrap_components as dbc
import dash.exceptions

pytestmark = pytest.mark.component


class TestXlsxExportButton:
    def test_create_xlsx_export_button_returns_button(self):
        from common.html_elements.grid_export import create_xlsx_export_button

        button = create_xlsx_export_button("test-btn")
        assert isinstance(button, dbc.Button)
        assert button.children == "Export xlsx"
        assert button.id == "test-btn"
        assert button.color == "secondary"
        assert button.outline is True


class TestRowdataToXlsxDownload:
    def test_with_valid_row_data_returns_download_dict(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        row_data = [
            {"col1": "value1", "col2": 10},
            {"col1": "value2", "col2": 20},
        ]
        result = rowdata_to_xlsx_download(row_data, "test.xlsx", "test_sheet")

        # dcc.send_data_frame returns a dict with base64 content
        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "test.xlsx"
        assert "content" in result or "base64" in result

    def test_with_empty_row_data_raises_prevent_update(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        with pytest.raises(dash.exceptions.PreventUpdate):
            rowdata_to_xlsx_download([], "test.xlsx")

    def test_with_none_row_data_raises_prevent_update(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        with pytest.raises(dash.exceptions.PreventUpdate):
            rowdata_to_xlsx_download(None, "test.xlsx")


class TestComparePageExportCallback:
    """
    Compare page has one grid with xlsx export: statistics table.
    """

    def test_statistics_export_returns_download_object_on_click(self):
        from pages.compare.compare import export_statistics_xlsx

        row_data = [{"metric": "CAGR", "value": 0.08}]
        result = export_statistics_xlsx(1, row_data)

        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "compare_statistics.xlsx"


class TestPortfolioPageExportCallbacks:
    """
    Portfolio page has three grids with xlsx export: describe statistics,
    survival statistics (MC forecast branch), and wealth statistics (MC forecast branch).
    Each has its own export callback wired to the grid_export helper.
    """

    def test_statistics_export_returns_download_object_on_click(self):
        from pages.portfolio.portfolio import export_pf_statistics_xlsx

        row_data = [{"metric": "CAGR", "value": 0.10}]
        result = export_pf_statistics_xlsx(1, row_data)

        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "portfolio_statistics.xlsx"

    def test_survival_statistics_export_returns_download_object_on_click(self):
        from pages.portfolio.portfolio import export_pf_survival_statistics_xlsx

        row_data = [{"probability": 0.95, "years": 25}]
        result = export_pf_survival_statistics_xlsx(1, row_data)

        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "survival_statistics.xlsx"

    def test_wealth_statistics_export_returns_download_object_on_click(self):
        from pages.portfolio.portfolio import export_pf_wealth_statistics_xlsx

        row_data = [{"percentile": 50, "wealth": 100000}]
        result = export_pf_wealth_statistics_xlsx(1, row_data)

        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "wealth_statistics.xlsx"

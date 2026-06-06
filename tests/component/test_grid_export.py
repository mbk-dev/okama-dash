"""
Component tests for grid xlsx export helper.
"""

import base64
import io

import pytest
import dash_bootstrap_components as dbc
import dash.exceptions
import openpyxl

pytestmark = pytest.mark.component


def _load_sheet(download_dict):
    """Decode a dcc.Download dict and return the active openpyxl worksheet."""
    content = base64.b64decode(download_dict["content"])
    workbook = openpyxl.load_workbook(io.BytesIO(content))
    return workbook.active


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
        result = rowdata_to_xlsx_download(1, row_data, "test.xlsx", "test_sheet")

        # dcc.send_data_frame returns a dict with base64 content
        assert isinstance(result, dict)
        assert "filename" in result
        assert result["filename"] == "test.xlsx"
        assert "content" in result or "base64" in result

    def test_with_empty_row_data_raises_prevent_update(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        with pytest.raises(dash.exceptions.PreventUpdate):
            rowdata_to_xlsx_download(1, [], "test.xlsx")

    def test_with_none_row_data_raises_prevent_update(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        with pytest.raises(dash.exceptions.PreventUpdate):
            rowdata_to_xlsx_download(1, None, "test.xlsx")

    def test_without_click_raises_prevent_update(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        with pytest.raises(dash.exceptions.PreventUpdate):
            rowdata_to_xlsx_download(None, [{"col1": "value1"}], "test.xlsx")


class TestColumnFormats:
    """
    Exported numbers must look like the on-page grid: percent columns get the
    Excel number format 0.00% (value stays numeric), decimal columns 0.00,
    integer columns #,##0. Cells keep raw values so Excel formulas still work.
    """

    def test_percent_column_gets_excel_percent_format_and_keeps_raw_value(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        row_data = [{"property": "CAGR", "PORTFOLIO.PF": 0.206}]
        result = rowdata_to_xlsx_download(
            1, row_data, "test.xlsx", column_formats={"PORTFOLIO.PF": "percent"}
        )

        sheet = _load_sheet(result)
        cell = sheet["B2"]  # column B = PORTFOLIO.PF, row 2 = first data row
        assert cell.value == 0.206
        assert cell.number_format == "0.00%"

    def test_decimal_and_int_formats_apply_to_their_columns(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        row_data = [{"1": "Mean", "2": 19.0999, "3": 3568.4}]
        result = rowdata_to_xlsx_download(
            1, row_data, "test.xlsx", column_formats={"2": "decimal", "3": "int"}
        )

        sheet = _load_sheet(result)
        assert sheet["B2"].number_format == "0.00"
        assert sheet["C2"].number_format == "#,##0"

    def test_unmapped_columns_keep_general_format(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        row_data = [{"property": "CAGR", "PORTFOLIO.PF": 0.206}]
        result = rowdata_to_xlsx_download(
            1, row_data, "test.xlsx", column_formats={"PORTFOLIO.PF": "percent"}
        )

        sheet = _load_sheet(result)
        assert sheet["A2"].number_format == "General"

    def test_without_column_formats_keeps_plain_export(self):
        from common.html_elements.grid_export import rowdata_to_xlsx_download

        row_data = [{"property": "CAGR", "PORTFOLIO.PF": 0.206}]
        result = rowdata_to_xlsx_download(1, row_data, "test.xlsx")

        sheet = _load_sheet(result)
        assert sheet["B2"].value == 0.206
        assert sheet["B2"].number_format == "General"


class TestPercentColumnFormats:
    """percent_column_formats builds the describe-table mapping: every column
    except the label columns (property, period) is a percent column."""

    def test_excludes_property_and_period(self):
        from common.html_elements.grid_export import percent_column_formats

        row_data = [{"property": "CAGR", "period": "1 years", "PORTFOLIO.PF": 0.2, "inflation": 0.03}]
        assert percent_column_formats(row_data) == {"PORTFOLIO.PF": "percent", "inflation": "percent"}

    def test_returns_none_for_empty_row_data(self):
        from common.html_elements.grid_export import percent_column_formats

        assert percent_column_formats([]) is None
        assert percent_column_formats(None) is None


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

    def test_statistics_export_formats_metric_columns_as_percent(self):
        from pages.compare.compare import export_statistics_xlsx

        row_data = [{"property": "CAGR", "period": "1 years", "SPY.US": 0.206, "inflation": 0.03}]
        result = export_statistics_xlsx(1, row_data)

        sheet = _load_sheet(result)
        assert sheet["C2"].number_format == "0.00%"  # SPY.US
        assert sheet["D2"].number_format == "0.00%"  # inflation
        assert sheet["A2"].number_format == "General"  # property stays text


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

    def test_statistics_export_formats_metric_columns_as_percent(self):
        from pages.portfolio.portfolio import export_pf_statistics_xlsx

        row_data = [{"property": "CAGR", "period": "1 years", "PORTFOLIO.PF": 0.206}]
        result = export_pf_statistics_xlsx(1, row_data)

        sheet = _load_sheet(result)
        assert sheet["C2"].value == 0.206
        assert sheet["C2"].number_format == "0.00%"

    def test_survival_statistics_export_formats_value_columns_as_decimal(self):
        from pages.portfolio.portfolio import export_pf_survival_statistics_xlsx

        # Desktop layout: 1/3 = labels, 2/4 = survival periods in years
        row_data = [{"1": "1st percentile", "2": 19.0999, "3": "Min", "4": 19.0999}]
        result = export_pf_survival_statistics_xlsx(1, row_data)

        sheet = _load_sheet(result)
        assert sheet["B2"].number_format == "0.00"
        assert sheet["D2"].number_format == "0.00"
        assert sheet["A2"].number_format == "General"

    def test_wealth_statistics_export_formats_value_columns_as_grouped_int(self):
        from pages.portfolio.portfolio import export_pf_wealth_statistics_xlsx

        # Desktop layout: 1/4 = labels, 2/3/5/6 = FV/PV wealth amounts
        row_data = [{"1": "Mean", "2": 6794.2, "3": 5032.7, "4": "Std", "5": 2795.1, "6": 2070.3}]
        result = export_pf_wealth_statistics_xlsx(1, row_data)

        sheet = _load_sheet(result)
        for col in ("B", "C", "E", "F"):
            assert sheet[f"{col}2"].number_format == "#,##0", col
        assert sheet["A2"].number_format == "General"

    # The survival/wealth export buttons are created dynamically on Submit;
    # Dash fires their callbacks on first render (prevent_initial_call does not
    # apply to components inserted after page load), so n_clicks=None must not
    # trigger a download — otherwise every MC Submit auto-downloads two files.
    def test_survival_statistics_export_prevents_update_without_click(self):
        from pages.portfolio.portfolio import export_pf_survival_statistics_xlsx

        with pytest.raises(dash.exceptions.PreventUpdate):
            export_pf_survival_statistics_xlsx(None, [{"probability": 0.95, "years": 25}])

    def test_wealth_statistics_export_prevents_update_without_click(self):
        from pages.portfolio.portfolio import export_pf_wealth_statistics_xlsx

        with pytest.raises(dash.exceptions.PreventUpdate):
            export_pf_wealth_statistics_xlsx(None, [{"percentile": 50, "wealth": 100000}])

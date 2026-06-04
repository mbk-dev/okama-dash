"""
Component tests for grid CSV export helper.
"""

import pytest
import dash_bootstrap_components as dbc

pytestmark = pytest.mark.component


class TestCsvExportButton:
    def test_create_csv_export_button_returns_button(self):
        from common.html_elements.grid_export import create_csv_export_button

        button = create_csv_export_button("test-btn")
        assert isinstance(button, dbc.Button)
        assert button.children == "Export CSV"
        assert button.id == "test-btn"
        assert button.color == "secondary"
        assert button.outline is True


class TestCsvExportCallback:
    def test_callback_returns_true_on_click(self):
        from common.html_elements.grid_export import csv_export_callback

        # Invoke with n_clicks > 0
        result = csv_export_callback(1)
        assert result is True

    def test_callback_returns_false_on_zero_clicks(self):
        from common.html_elements.grid_export import csv_export_callback

        # Invoke with n_clicks = 0 or None
        assert csv_export_callback(0) is False
        assert csv_export_callback(None) is False


class TestPortfolioGridExportCallbacks:
    """
    Portfolio page has three grids with CSV export: describe statistics,
    survival statistics (MC forecast branch), and wealth statistics (MC forecast branch).
    Each has its own export callback wired to the grid_export helper.
    """

    def test_statistics_export_triggers_on_button_click(self):
        from pages.portfolio.portfolio import export_pf_statistics_csv

        result = export_pf_statistics_csv(1)
        assert result is True

    def test_survival_statistics_export_triggers_on_button_click(self):
        from pages.portfolio.portfolio import export_pf_survival_statistics_csv

        result = export_pf_survival_statistics_csv(1)
        assert result is True

    def test_wealth_statistics_export_triggers_on_button_click(self):
        from pages.portfolio.portfolio import export_pf_wealth_statistics_csv

        result = export_pf_wealth_statistics_csv(1)
        assert result is True

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

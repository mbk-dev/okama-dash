import plotly.graph_objects as go
import pytest

from common.chart_helpers import add_return_type_annotation

pytestmark = pytest.mark.unit


class TestFormatPoints:
    def test_rounds_to_integer_and_separates_thousands_with_space(self):
        from common.chart_helpers import format_points

        assert format_points(13456.78) == "13 457"

    def test_value_below_thousand_has_no_separator(self):
        from common.chart_helpers import format_points

        assert format_points(999.4) == "999"

    def test_millions_get_two_separators(self):
        from common.chart_helpers import format_points

        assert format_points(1234567.89) == "1 234 568"


class TestAddReturnTypeAnnotation:
    def test_adds_cagr_note(self):
        fig = go.Figure()
        add_return_type_annotation(fig, "CAGR")
        texts = [a.text for a in fig.layout.annotations]
        assert any("CAGR" in t for t in texts)

    def test_defaults_to_cagr(self):
        fig = go.Figure()
        add_return_type_annotation(fig)
        assert "CAGR" in fig.layout.annotations[0].text

    def test_annotation_is_a_note_without_arrow(self):
        fig = go.Figure()
        add_return_type_annotation(fig)
        assert fig.layout.annotations[0].showarrow is False

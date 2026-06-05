import plotly.graph_objects as go
import pytest

from pages.efficient_frontier.prepare_ef_plot import _accumulate_label_padding

pytestmark = pytest.mark.unit


def _fig_with_label(textposition: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[1.0],
            y=[2.0],
            mode="markers+text",
            text=["AGG.US"],
            textposition=textposition,
        )
    )
    return fig


def test_center_position_reserves_half_label_width_on_both_sides():
    # "top center" labels (mobile/compact mode) hang half their width over
    # each side of the data point, so both paddings must be reserved.
    fig = _fig_with_label("top center")
    left, right = _accumulate_label_padding(fig, base_padding=1.0, char_padding=0.1)
    expected = (1.0 + 0.1 * len("AGG.US")) / 2
    assert left == pytest.approx(expected)
    assert right == pytest.approx(expected)


def test_left_position_reserves_full_label_width_on_left_only():
    fig = _fig_with_label("top left")
    left, right = _accumulate_label_padding(fig, base_padding=1.0, char_padding=0.1)
    assert left == pytest.approx(1.0 + 0.1 * len("AGG.US"))
    assert right == 0.0

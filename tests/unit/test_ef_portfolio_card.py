import pytest

pytestmark = pytest.mark.unit


def _walk(component):
    """Yield the component and all its descendants (components and strings)."""
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        yield from _walk(child)


def _by_class(component, css_class):
    return [node for node in _walk(component) if css_class in (getattr(node, "className", "") or "").split()]


def _texts(component):
    return [node for node in _walk(component) if isinstance(node, str)]


class TestBuildPortfolioCard:
    def test_renders_stat_blocks_with_labels_and_values(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[("CAGR", "10.00%"), ("Risk Σ", "15.00%"), ("Sharpe", "0.67")],
            symbols=["SPY.US"],
            weights=[100.0],
        )

        assert len(_by_class(card, "pf-stat")) == 3
        texts = _texts(card)
        for expected in ("CAGR", "10.00%", "Risk Σ", "15.00%", "Sharpe", "0.67"):
            assert expected in texts

    def test_default_title_is_selected_portfolio(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(stats=[], symbols=["SPY.US"], weights=[100.0])

        titles = _by_class(card, "pf-card-title")
        assert len(titles) == 1
        assert titles[0].children == "Selected portfolio"

    def test_custom_title_and_badge(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[],
            symbols=["SPY.US"],
            weights=[100.0],
            badge="Efficient Frontier",
            title="Optimized portfolio",
        )

        assert _by_class(card, "pf-card-title")[0].children == "Optimized portfolio"
        badges = _by_class(card, "pf-card-badge")
        assert len(badges) == 1
        assert badges[0].children == "Efficient Frontier"

    def test_no_badge_element_when_badge_is_none(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(stats=[], symbols=["SPY.US"], weights=[100.0])

        assert _by_class(card, "pf-card-badge") == []

    def test_one_asset_row_per_symbol_with_percent_and_bar_width(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[],
            symbols=["SPY.US", "BND.US"],
            weights=[60.0, 40.0],
        )

        rows = _by_class(card, "pf-asset-row")
        assert len(rows) == 2
        texts = _texts(card)
        assert "SPY.US" in texts
        assert "BND.US" in texts
        assert "60.00%" in texts
        assert "40.00%" in texts
        fills = _by_class(card, "pf-asset-fill")
        widths = [float(fill.style["width"].rstrip("%")) for fill in fills]
        assert widths == pytest.approx([60.0, 40.0])

    def test_stacked_bar_skips_zero_weight_segments(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[],
            symbols=["AAPL.US", "MSFT.US", "GOOG.US"],
            weights=[0.0, 100.0, 0.0],
        )

        segments = _by_class(card, "pf-alloc-segment")
        assert len(segments) == 1
        assert float(segments[0].style["width"].rstrip("%")) == pytest.approx(100.0)
        # All three assets still get a row (with an empty bar)
        assert len(_by_class(card, "pf-asset-row")) == 3

    def test_asset_colors_follow_plotly_palette_and_cycle(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            ASSET_COLORS,
            asset_color,
        )

        assert asset_color(0) == ASSET_COLORS[0]
        assert asset_color(1) == ASSET_COLORS[1]
        assert asset_color(len(ASSET_COLORS)) == ASSET_COLORS[0]

    def test_dot_fill_and_segment_share_the_asset_color(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            asset_color,
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[],
            symbols=["SPY.US", "BND.US"],
            weights=[60.0, 40.0],
        )

        dots = _by_class(card, "pf-asset-dot")
        fills = _by_class(card, "pf-asset-fill")
        segments = _by_class(card, "pf-alloc-segment")
        for index in range(2):
            expected = asset_color(index)
            assert dots[index].style["backgroundColor"] == expected
            assert fills[index].style["backgroundColor"] == expected
            assert segments[index].style["backgroundColor"] == expected

    def test_none_weights_render_note_instead_of_allocation(self):
        from pages.efficient_frontier.cards_efficient_frontier.ef_portfolio_card import (
            build_portfolio_card,
        )

        card = build_portfolio_card(
            stats=[("CAGR", "10.00%")],
            symbols=["SPY.US", "BND.US"],
            weights=None,
            note="Weights: unavailable for this point.",
        )

        notes = _by_class(card, "pf-note")
        assert len(notes) == 1
        assert notes[0].children == "Weights: unavailable for this point."
        assert _by_class(card, "pf-alloc-bar") == []
        assert _by_class(card, "pf-asset-row") == []

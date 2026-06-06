"""Styled portfolio card shared by the EF click-data and Find-portfolio sections."""

from dash import html
import plotly.express as px

# The same qualitative palette px assigns to assets in the transition map,
# so dots and bars match the asset colors used elsewhere on the page.
ASSET_COLORS = px.colors.qualitative.Plotly


def asset_color(index: int) -> str:
    """Color for the asset at the given index, cycling through the palette."""
    return ASSET_COLORS[index % len(ASSET_COLORS)]


def build_portfolio_card(
    stats: list[tuple[str, str]],
    symbols: list[str],
    weights: list[float] | None,
    badge: str | None = None,
    title: str = "Selected portfolio",
    note: str | None = None,
) -> html.Div:
    """Assemble the portfolio card: header, stat blocks and allocation bars.

    stats: (label, formatted value) pairs, e.g. ("CAGR", "30.40%").
    weights: per-asset weights in percent, aligned with symbols; None renders
    the note instead of the allocation block.
    """
    header_children = [html.Span(title, className="pf-card-title")]
    if badge:
        header_children.append(html.Span(badge, className="pf-card-badge"))
    blocks = [
        html.Div(header_children, className="pf-card-header"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(label, className="pf-stat-label"),
                        html.Div(value, className="pf-stat-value"),
                    ],
                    className="pf-stat",
                )
                for label, value in stats
            ],
            className="pf-stats",
        ),
    ]
    if weights is None:
        blocks.append(html.P(note, className="pf-note text-muted"))
    else:
        blocks.append(_build_allocation(symbols, weights))
    return html.Div(blocks, className="pf-card")


def _build_allocation(symbols: list[str], weights: list[float]) -> html.Div:
    segments = [
        html.Div(
            className="pf-alloc-segment",
            style={"width": f"{weight}%", "backgroundColor": asset_color(index)},
        )
        for index, weight in enumerate(weights)
        if weight > 0
    ]
    rows = [
        html.Div(
            [
                html.Span(
                    className="pf-asset-dot",
                    style={"backgroundColor": asset_color(index)},
                ),
                html.Span(symbol, className="pf-asset-name"),
                html.Div(
                    html.Div(
                        className="pf-asset-fill",
                        style={"width": f"{weight}%", "backgroundColor": asset_color(index)},
                    ),
                    className="pf-asset-track",
                ),
                html.Span(f"{weight:.2f}%", className="pf-asset-pct"),
            ],
            className="pf-asset-row",
        )
        for index, (symbol, weight) in enumerate(zip(symbols, weights, strict=True))
    ]
    return html.Div(
        [
            html.Div("Allocation", className="pf-stat-label"),
            html.Div(segments, className="pf-alloc-bar"),
            html.Div(rows, className="pf-asset-rows"),
        ],
        className="pf-allocation",
    )

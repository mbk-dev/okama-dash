def is_small_screen(screen: dict | None) -> bool:
    """True when the client viewport is narrower than the mobile breakpoint."""
    return bool(screen and screen["in_width"] < 800)


def adopt_small_screens(fig, screen: dict):
    """
    Change Figure and Graph config for small screens.
    """
    if is_small_screen(screen):
        fig.update_layout(
            # Legend below the chart: "container" ref pins it to the bottom edge
            # and lets plotly auto-expand the margin so it never overlaps the plot.
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "yref": "container",
                "y": 0,
                "xanchor": "left",
                "xref": "container",
                "x": 0,
                # Horizontal legends put the title on the left by default,
                # stealing width from every row; move it to its own row.
                "title": {"side": "top"},
            },
            margin={"l": 0, "r": 0, "t": 40, "b": 24, "pad": 0},
        )
        fig.update_yaxes(
            title_text=None,
            title_standoff=0,
            visible=True,
            # Tick labels inside the plot area: frees the left gutter so the
            # chart can stretch edge to edge while the scale stays readable.
            ticklabelposition="inside",
        )
        config = {"displayModeBar": False, "displaylogo": False}
    else:
        fig.update_layout(
            margin={"pad": 3},
        )
        config = {"displayModeBar": True, "displaylogo": False}
    return fig, config

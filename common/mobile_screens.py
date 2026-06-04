def adopt_small_screens(fig, screen: dict):
    """
    Change Figure and Graph config for small screens.
    """
    if screen and screen["in_width"] < 800:
        fig.update_layout(
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0,
            },
            margin={"l": 8, "r": 8, "t": 80, "b": 24, "pad": 0},
        )
        fig.update_yaxes(
            # tickangle=90,
            title_text=None,
            # title_font={"size": 8},
            title_standoff=0,
            visible=True,
        )
        config = {"displayModeBar": False, "displaylogo": False}
    else:
        fig.update_layout(
            margin={"pad": 3},
        )
        config = {"displayModeBar": True, "displaylogo": False}
    return fig, config

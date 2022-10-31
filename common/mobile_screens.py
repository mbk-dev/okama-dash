def adopt_small_screens(fig, screen: dict):
    """
    Change Figure and Graph config for small screens.
    """
    if screen and screen["in_width"] < 800:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=20, b=20, pad=3),
        )
        fig.update_yaxes(
            # tickangle=90,
            title_text="",
            # title_font={"size": 8},
            title_standoff=0,
            visible=True,
        )
        config = {"displayModeBar": False, "displaylogo": False}
    else:
        fig.update_layout(
            margin=dict(pad=3),
        )
        config = {"displayModeBar": True, "displaylogo": False}
    return fig, config

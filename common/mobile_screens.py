def adopt_small_screens(fig, screen: dict):
    """
    Change Figure and Graph config for small screens.
    """
    if screen and screen["in_width"] < 800:
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1),
            margin=dict(l=0, r=0, t=20, b=20),
        )
        config = {'displayModeBar': False,
                  'displaylogo': False}
    else:
        config = {'displayModeBar': True,
                  'displaylogo': False}
    return fig, config

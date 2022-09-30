import dash_bootstrap_components as dbc
from dash import html, dcc


def create_copy_link_div(location_id: str, hidden_div_with_url_id: str, button_id: str, card_name: str):
    return html.Div(
        [
            # the URL bar, doesn't render anything
            dcc.Location(id=location_id, refresh=False),
            # copy link button
            html.Div(
                [
                    dbc.Button(
                        [
                            "Copy link",
                            html.I(className="bi bi-share ms-2"),
                            dcc.Clipboard(
                                target_id=hidden_div_with_url_id,
                                # remove default html.Clipboard icon
                                className="position-absolute start-0 top-0 h-100 w-100 opacity-0",
                            ),
                        ],
                        id=button_id,
                        className="position-relative",
                        color="link",
                        outline=False,
                    ),
                    # hidden div to receive output from callback with url
                    html.Div(
                        children="", hidden=True, id=hidden_div_with_url_id
                    ),
                    dbc.Tooltip(
                        f"Copy {card_name} link to clipboard",
                        target=button_id,
                    ),
                ],
                style={"text-align": "center"},
            ),
        ]
    )

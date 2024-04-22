from typing import Optional


def change_style_for_hidden_row(n_clicks: int, style: Optional[dict]) -> Optional[dict]:
    if n_clicks != 0:
        style = None
    elif n_clicks == 0 and not style:
        style = {"display": "none"}
    return style

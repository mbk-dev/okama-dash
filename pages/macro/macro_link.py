"""Shareable-link builder for macro pages.

Macro URLs are flat (tickers + dates + small page params), unlike the
portfolio link builder in common/create_link.py with its strategy scoping —
a dedicated tiny builder keeps both readable. Values equal to the page
default (or falsy) are omitted, mirroring the site-wide skip_if_default rule.
"""

import pandas as pd

from pages.macro.macro_data import MACRO_FIRST_DATE_DEFAULT


def build_macro_link(
    *,
    href: str,
    tickers_list: list[str],
    first_date: str | None,
    last_date: str | None,
    **extra: tuple[str | None, str | None],
) -> str:
    """Build "<path>?tickers=...&..." keeping only non-default params.

    extra: page params as name=(value, default) pairs.
    """
    today_str = pd.Timestamp.today().strftime("%Y-%m")
    reset_href = href.split("?")[0]
    parts = [f"{reset_href}?tickers=" + ",".join(tickers_list)]
    if first_date and first_date != MACRO_FIRST_DATE_DEFAULT:
        parts.append(f"first_date={first_date}")
    if last_date and last_date != today_str:
        parts.append(f"last_date={last_date}")
    for name, (value, default) in extra.items():
        if value and value != default:
            parts.append(f"{name}={value}")
    return "&".join(parts)

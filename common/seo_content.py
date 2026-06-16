"""Per-route crawler body content (issue #29, increment B).

The section pages each render an on-screen description card whose text lives as a
dcc.Markdown in pages/*/cards_*/eng/*_description_txt.py. To give no-JS crawlers
real, indexable body text (injected by common.seo into the React mount point), we
reuse that same Markdown — one source of truth — and render it to HTML here.

We render a minimal Markdown subset (headings, bullet lists with indented
continuation lines, paragraphs, bold, italic) ourselves instead of adding a
Markdown dependency: secondvds keeps its own gitignored poetry.lock, so a new
dependency would make the deploy's `poetry install` inconsistent with the lock
and abort the auto-deploy. The descriptions only use this subset.
"""

import re
from html import escape
from textwrap import dedent

from pages.benchmark.cards_benchmark.eng.benchmark_description_txt import benchmark_description_text
from pages.compare.cards_compare.eng.compare_description_txt import compare_description_text
from pages.database.cards_database.eng.db_description_txt import db_description_text
from pages.efficient_frontier.cards_efficient_frontier.eng.ef_description_txt import (
    ef_description_text,
)
from pages.macro.cards_macro.eng.cape10_description_txt import cape10_description_text
from pages.macro.cards_macro.eng.inflation_description_txt import inflation_description_text
from pages.macro.cards_macro.eng.rates_description_txt import rates_description_text
from pages.macro.cards_macro.eng.real_estate_description_txt import real_estate_description_text
from pages.portfolio.cards_portfolio.eng.portfolio_description_txt import portfolio_description_text


def _inline(text: str) -> str:
    """Escape text, then render **bold** and *italic* (bold first)."""
    text = escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def render_markdown(md: str) -> str:
    """Render the small Markdown subset used by the section description cards.

    Supports `#` headings (-> <h2>), `- ` bullet lists with indented continuation
    lines, soft-wrapped paragraphs (blank line = block break), bold and italic.
    """
    blocks: list[str] = []
    para: list[str] = []
    bullets: list[str] = []

    def flush_para() -> None:
        if para:
            blocks.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def flush_bullets() -> None:
        if bullets:
            blocks.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for raw in dedent(md).splitlines():
        stripped = raw.strip()
        if not stripped:
            flush_para()
            flush_bullets()
        elif stripped.startswith("#"):
            flush_para()
            flush_bullets()
            blocks.append(f"<h2>{_inline(stripped.lstrip('#').strip())}</h2>")
        elif stripped.startswith("- "):
            flush_para()
            bullets.append(_inline(stripped[2:].strip()))
        elif bullets and raw[:1].isspace():
            bullets[-1] += " " + _inline(stripped)  # continuation of the last bullet
        else:
            flush_bullets()
            para.append(_inline(stripped))

    flush_para()
    flush_bullets()
    return "".join(blocks)


# Route path -> the page's description dcc.Markdown (raw Markdown in .children).
_ROUTE_DESCRIPTION = {
    "/": ef_description_text,
    "/portfolio": portfolio_description_text,
    "/compare": compare_description_text,
    "/benchmark": benchmark_description_text,
    "/database": db_description_text,
    "/macro/inflation": inflation_description_text,
    "/macro/rates": rates_description_text,
    "/macro/cape10": cape10_description_text,
    "/macro/real-estate": real_estate_description_text,
}

# Rendered once at import; common.seo injects SEO_BODY_HTML[path] for crawlers.
SEO_BODY_HTML: dict[str, str] = {
    path: render_markdown(component.children) for path, component in _ROUTE_DESCRIPTION.items()
}

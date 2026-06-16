"""Server-side SEO head fixups for crawlers and link unfurlers.

okama.io is a client-rendered Dash SPA: the static HTML served to a crawler (or
to a social/chat link unfurler, which never runs JS) carries app.title ("Dash")
as the literal <title>, has no <link rel="canonical">, and — because no page
sets a register_page image — ships empty og:image/twitter:image tags. The real
per-page title and share preview only ever appear once Dash's JS runs, so a
weak-JS crawler (notably Yandex) and every unfurler see "Dash" with no preview.

This Flask after_request hook rewrites the served HTML of page routes so the
static markup already carries the per-page <title> (from dash.page_registry), a
canonical URL for the clean section (query string stripped, so shareable links
with ?tickers=... canonicalize onto the bare section), a default share image,
and per-page crawler body content (issue #29). Callback POSTs (application/json)
and static assets are left untouched.

Crawler body content: the SPA serves a near-empty <body> (just the React mount
placeholder), so a weak-JS crawler indexes no section text. Dash has no native
SSR, but the React renderer replaces the children of <div id="react-entry-point">
on hydration — so injecting the page heading + description there is seen only by
no-JS clients and overwritten for real users. It is not cloaking: the same text
appears in the page's on-screen description card.

Why set og:image here instead of passing meta_tags to Dash(): Dash always
emits its own og:image/twitter:image from the page registry, and app-level
meta_tags are appended *after* those — so a meta_tags default produces a
duplicate tag (verified against dash 4.2.0). Dash also auto-infers a site-wide
image from assets/logo.png (its generic fallback name), which would otherwise
put the square logo at a request-scheme (http, no ProxyFix) URL into the social
card. So the hook overrides og:image/twitter:image in place with the dedicated
1200x630 share card — single tag, fixed https URL, immune to auto-infer.
"""

import re
from html import escape

import dash
from flask import Flask

from common.seo_content import SEO_BODY_HTML

SITE_ORIGIN = "https://okama.io"
DEFAULT_SHARE_IMAGE = f"{SITE_ORIGIN}/assets/og-image.png"

_TITLE_RE = re.compile(r"<title>.*?</title>", re.S)
_OG_IMAGE_RE = re.compile(r'(<meta property="og:image" content=")[^"]*(">)')
_TW_IMAGE_RE = re.compile(r'(<meta property="twitter:image" content=")[^"]*(">)')


def _crawler_body(page: dict) -> str:
    """Build the no-JS crawler content injected into the React mount point.

    Heading (the page name) + the section's rendered description (common.seo_content,
    reused from the on-screen description card); falls back to the short registry
    description for routes without a rendered body. React overwrites it on
    hydration, so it is visible only to clients that don't run JS.
    """
    heading = escape(page.get("name") or page.get("title") or "okama")
    body = SEO_BODY_HTML.get(page.get("path", "")) or (
        f"<p>{escape(' '.join((page.get('description') or '').split()))}</p>"
    )
    return f'<div id="seo-content"><h1>{heading}</h1>{body}</div>'


def _page_for_path(path: str) -> dict | None:
    """Match a request path against page_registry, ignoring a trailing slash."""
    normalized = path.rstrip("/") or "/"
    return next(
        (
            page
            for page in dash.page_registry.values()
            if (page["path"].rstrip("/") or "/") == normalized
        ),
        None,
    )


def register_seo_head(server: Flask) -> None:
    @server.after_request
    def _seo_head(response):
        # Only HTML page documents; callbacks are application/json, assets are
        # css/js/images — none start with text/html.
        if not (response.content_type or "").startswith("text/html"):
            return response

        from flask import request

        page = _page_for_path(request.path)
        if page is None:
            return response

        html = response.get_data(as_text=True)

        # Per-page <title> (Dash leaves the static <title> as app.title "Dash").
        # A lambda replacement keeps any backslash/% in the title literal.
        title = page.get("title") or "okama"
        html = _TITLE_RE.sub(lambda _m: f"<title>{title}</title>", html, count=1)

        # Canonical for the clean section, without query params, idempotent.
        if 'rel="canonical"' not in html:
            canonical = SITE_ORIGIN + (request.path.rstrip("/") or "/")
            html = html.replace(
                "</head>",
                f'<link rel="canonical" href="{canonical}"/>\n</head>',
                1,
            )

        # Override Dash's share-image tags in place (see module docstring); a
        # lambda replacement keeps the URL literal regardless of its content.
        html = _OG_IMAGE_RE.sub(lambda m: f"{m.group(1)}{DEFAULT_SHARE_IMAGE}{m.group(2)}", html)
        html = _TW_IMAGE_RE.sub(lambda m: f"{m.group(1)}{DEFAULT_SHARE_IMAGE}{m.group(2)}", html)

        # Crawler body content: inject heading + description as the first child of
        # the React mount; React overwrites it on hydration (see module docstring).
        html = html.replace(
            '<div id="react-entry-point">',
            f'<div id="react-entry-point">{_crawler_body(page)}',
            1,
        )

        response.set_data(html)
        return response

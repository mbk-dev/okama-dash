"""Server-side SEO head fixups: per-page <title>, canonical, default share image.

A JS-less crawler/unfurler gets the static HTML Dash serves, where it leaves
app.title ("Dash") as the literal <title>, omits <link rel="canonical">, and —
because no page supplies a register_page image — emits empty og:image/
twitter:image tags. register_seo_head rewrites page-route HTML so the static
markup already carries the per-page title (from dash.page_registry), a
query-stripped canonical, and a default share image, without touching callback
JSON or assets.
"""

import dash
import flask
import pytest

from common.seo import DEFAULT_SHARE_IMAGE, register_seo_head

pytestmark = pytest.mark.component

# Mirrors the static HTML Dash serves for a page route. og:image/twitter:image
# carry the URL Dash auto-infers from assets/logo.png (its generic site-wide
# image) — the hook must override that square logo with the 1200x630 share card.
DASH_INDEX_HTML = (
    '<!DOCTYPE html>\n<html lang="en">\n    <head>\n'
    '        <meta name="description" content="x">\n'
    '      <meta property="twitter:image" content="http://localhost/assets/logo.png">\n'
    '      <meta property="og:image" content="http://localhost/assets/logo.png">\n'
    "        <title>Dash</title>\n    </head>\n    <body>app</body>\n</html>"
)

FAKE_REGISTRY = {
    "pages.portfolio.portfolio": {"path": "/portfolio", "title": "Investment Portfolio : okama"},
    "pages.efficient_frontier.frontier": {"path": "/", "title": "Efficient Frontier : okama"},
}


@pytest.fixture()
def client(monkeypatch):
    # The hook reads dash.page_registry at request time; a fake keeps the test
    # isolated from the real pages (and from polluting the global registry).
    monkeypatch.setattr(dash, "page_registry", FAKE_REGISTRY)
    server = flask.Flask("seo_test")

    def _html_page():
        return flask.Response(DASH_INDEX_HTML, content_type="text/html; charset=utf-8")

    server.add_url_rule("/portfolio", "portfolio", _html_page)
    server.add_url_rule("/", "home", _html_page)
    server.add_url_rule("/unknown", "unknown", _html_page)
    server.add_url_rule(
        "/_dash-update-component",
        "callback",
        lambda: flask.Response('{"x":1}', content_type="application/json"),
        methods=["POST"],
    )

    register_seo_head(server)
    return server.test_client()


class TestTitle:
    def test_replaces_dash_title_with_page_title(self, client):
        html = client.get("/portfolio").get_data(as_text=True)
        assert "<title>Investment Portfolio : okama</title>" in html
        assert "<title>Dash</title>" not in html


class TestCanonical:
    def test_inserts_canonical_for_page(self, client):
        html = client.get("/portfolio").get_data(as_text=True)
        assert '<link rel="canonical" href="https://okama.io/portfolio"/>' in html

    def test_home_canonical_is_root(self, client):
        html = client.get("/").get_data(as_text=True)
        assert '<link rel="canonical" href="https://okama.io/"/>' in html


class TestShareImage:
    def test_forces_og_and_twitter_image_to_share_card(self, client):
        # Dash auto-infers the square logo into both tags; the hook overrides
        # them with the 1200x630 share card regardless of Dash's value.
        html = client.get("/portfolio").get_data(as_text=True)
        assert f'<meta property="og:image" content="{DEFAULT_SHARE_IMAGE}">' in html
        assert f'<meta property="twitter:image" content="{DEFAULT_SHARE_IMAGE}">' in html
        assert "logo.png" not in html
        assert html.count("og:image") == 1
        assert html.count("twitter:image") == 1


class TestScope:
    def test_json_callback_response_untouched(self, client):
        resp = client.post("/_dash-update-component")
        assert resp.get_data(as_text=True) == '{"x":1}'

    def test_unknown_path_left_unmodified(self, client):
        html = client.get("/unknown").get_data(as_text=True)
        assert "<title>Dash</title>" in html
        assert "canonical" not in html

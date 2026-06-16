"""Per-route crawler body content (issue #29, increment B).

common.seo_content reuses the on-screen section description cards (dcc.Markdown
in pages/*/cards_*/eng/) as the single source of truth and renders a minimal
Markdown subset to HTML server-side — no Markdown dependency, because a new dep
would break the lockfile-pinned auto-deploy. These tests cover the renderer and
the assembled per-route map.
"""

import pytest

from common.seo_content import SEO_BODY_HTML, render_markdown

pytestmark = pytest.mark.unit

EXPECTED_ROUTES = {
    "/",
    "/portfolio",
    "/compare",
    "/benchmark",
    "/database",
    "/macro/inflation",
    "/macro/rates",
    "/macro/cape10",
    "/macro/real-estate",
}


class TestRenderMarkdown:
    def test_bold_becomes_strong(self):
        assert render_markdown("**bold** text") == "<p><strong>bold</strong> text</p>"

    def test_italic_becomes_em(self):
        assert render_markdown("*okama* db") == "<p><em>okama</em> db</p>"

    def test_heading_becomes_h2(self):
        assert render_markdown("##### Stock markets") == "<h2>Stock markets</h2>"

    def test_consecutive_bullets_become_one_list(self):
        assert render_markdown("- a\n- b") == "<ul><li>a</li><li>b</li></ul>"

    def test_indented_continuation_joins_previous_bullet(self):
        md = "- first line\n  continues here\n- second"
        assert render_markdown(md) == "<ul><li>first line continues here</li><li>second</li></ul>"

    def test_soft_wrapped_lines_join_into_one_paragraph(self):
        assert render_markdown("line one\nline two\n\nnext para") == (
            "<p>line one line two</p><p>next para</p>"
        )

    def test_html_special_chars_are_escaped(self):
        assert render_markdown("a < b & c") == "<p>a &lt; b &amp; c</p>"

    def test_common_source_indentation_is_stripped(self):
        # Description strings are indented by their Python triple-quote position.
        assert render_markdown("\n    para one\n    para two\n") == "<p>para one para two</p>"


class TestRouteBodyMap:
    def test_all_nine_routes_present(self):
        assert set(SEO_BODY_HTML) == EXPECTED_ROUTES

    def test_every_body_is_non_empty_html(self):
        for path, html in SEO_BODY_HTML.items():
            assert html.startswith("<"), path
            assert len(html) > 50, path

    def test_no_raw_markdown_markers_leak(self):
        for path, html in SEO_BODY_HTML.items():
            assert "**" not in html, path
            assert "\n- " not in html, path
            assert "#####" not in html, path

    def test_database_list_and_heading_rendered(self):
        html = SEO_BODY_HTML["/database"]
        assert "<h2>Stock markets</h2>" in html
        assert "<li>Mutual funds</li>" in html

    def test_benchmark_bullets_rendered(self):
        assert "<li>Tracking Difference</li>" in SEO_BODY_HTML["/benchmark"]

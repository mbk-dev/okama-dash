from unittest.mock import patch

import pytest

pytestmark = pytest.mark.component


def test_anonymous_sees_login_and_register():
    from navigation import render_auth_block

    with patch("navigation.user_is_authenticated", return_value=False):
        links = render_auth_block("/")
    rendered = str(links)
    assert "/login" in rendered
    assert "/register" in rendered
    assert "/cabinet" not in rendered


def test_authenticated_sees_cabinet_and_logout():
    from navigation import render_auth_block

    with patch("navigation.user_is_authenticated", return_value=True):
        links = render_auth_block("/portfolio")
    rendered = str(links)
    assert "/cabinet" in rendered
    assert "/logout" in rendered
    assert "/login" not in rendered


def test_logout_link_is_external_full_page_load():
    # /logout is a real Flask route: dcc client-side routing must NOT intercept it.
    from navigation import render_auth_block

    with patch("navigation.user_is_authenticated", return_value=True):
        links = render_auth_block("/portfolio")
    logout_link = next(link for link in links if getattr(link, "href", "") == "/logout")
    assert logout_link.external_link is True

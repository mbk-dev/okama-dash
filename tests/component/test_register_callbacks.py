from unittest.mock import MagicMock, patch

import dash
import pytest

pytestmark = pytest.mark.component


def test_successful_register_logs_in_and_redirects():
    from pages.register.register import do_register

    fake_user = MagicMock()
    with (
        patch("pages.register.register.create_user", return_value=(fake_user, None)) as create,
        patch("pages.register.register.login_user") as login,
    ):
        href, error = do_register(1, "a@b.co", "long-enough-pw", "long-enough-pw")
    create.assert_called_once_with("a@b.co", "long-enough-pw")
    login.assert_called_once_with(fake_user, remember=True)
    assert href == "/cabinet"
    assert error == ""


def test_password_mismatch_shows_error_without_creating_user():
    from pages.register.register import do_register

    with patch("pages.register.register.create_user") as create:
        href, error = do_register(1, "a@b.co", "long-enough-pw", "different-pw!")
    create.assert_not_called()
    assert href is dash.no_update
    assert "match" in error.lower()


def test_service_error_is_shown_inline():
    from pages.register.register import do_register

    with (
        patch("pages.register.register.create_user", return_value=(None, "This email is already registered.")),
        patch("pages.register.register.login_user") as login,
    ):
        href, error = do_register(1, "a@b.co", "long-enough-pw", "long-enough-pw")
    login.assert_not_called()
    assert href is dash.no_update
    assert error == "This email is already registered."

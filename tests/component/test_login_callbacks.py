from unittest.mock import MagicMock, patch

import dash
import pytest

pytestmark = pytest.mark.component


def test_valid_credentials_log_in_and_redirect():
    from pages.login.login import do_login

    fake_user = MagicMock()
    with (
        patch("pages.login.login.verify_credentials", return_value=fake_user),
        patch("pages.login.login.login_user") as login,
    ):
        href, error = do_login(1, "a@b.co", "long-enough-pw")
    login.assert_called_once_with(fake_user, remember=True)
    assert href == "/cabinet"
    assert error == ""


def test_invalid_credentials_show_neutral_error():
    from pages.login.login import do_login

    with (
        patch("pages.login.login.verify_credentials", return_value=None),
        patch("pages.login.login.login_user") as login,
    ):
        href, error = do_login(1, "a@b.co", "wrong")
    login.assert_not_called()
    assert href is dash.no_update
    # Neutral message: never reveals whether the email exists.
    assert error == "Wrong email or password."

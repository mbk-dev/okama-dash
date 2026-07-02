import pytest

from common.auth.helpers import current_user_id, user_is_authenticated
from common.auth.login_manager import load_user
from common.auth.service import create_user

pytestmark = pytest.mark.unit


def test_helpers_are_safe_outside_request_context():
    # Layout builders may run with no active request (imports, tooling) — never raise.
    assert user_is_authenticated() is False
    assert current_user_id() is None


def test_user_loader_returns_user_by_str_id(auth_app):
    user, _ = create_user("a@b.co", "long-enough-pw")
    assert load_user(str(user.id)).id == user.id


def test_user_loader_returns_none_for_unknown_id(auth_app):
    assert load_user("99999") is None

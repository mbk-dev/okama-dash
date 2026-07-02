import pytest

from common.auth.models import User
from common.auth.service import create_user, verify_credentials

pytestmark = pytest.mark.unit


class TestCreateUser:
    def test_creates_user_with_hashed_password(self, auth_app):
        user, error = create_user("New@Example.com", "long-enough-pw")
        assert error is None
        assert user.id is not None
        assert user.email == "new@example.com"  # normalized to lowercase
        assert user.password_hash != "long-enough-pw"  # never stored in plaintext

    def test_rejects_invalid_email(self, auth_app):
        user, error = create_user("not-an-email", "long-enough-pw")
        assert user is None
        assert "email" in error.lower()

    def test_rejects_short_password(self, auth_app):
        user, error = create_user("a@b.co", "short")
        assert user is None
        assert "8" in error

    def test_rejects_duplicate_email(self, auth_app):
        create_user("a@b.co", "long-enough-pw")
        user, error = create_user("A@B.CO", "another-long-pw")
        assert user is None
        assert "already registered" in error

    def test_rejects_overlong_password(self, auth_app):
        user, error = create_user("a@b.co", "x" * 129)
        assert user is None
        assert "128" in error


class TestVerifyCredentials:
    def test_valid_credentials_return_user(self, auth_app):
        created, _ = create_user("a@b.co", "long-enough-pw")
        user = verify_credentials("a@b.co", "long-enough-pw")
        assert isinstance(user, User)
        assert user.id == created.id

    def test_wrong_password_returns_none(self, auth_app):
        create_user("a@b.co", "long-enough-pw")
        assert verify_credentials("a@b.co", "wrong-password!") is None

    def test_unknown_email_returns_none(self, auth_app):
        assert verify_credentials("ghost@b.co", "whatever-long") is None

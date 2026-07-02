"""Auth business logic as pure functions — unit-testable without Dash or a browser.

Callbacks are thin wrappers around these; every DB write goes through _commit()
so a failure rolls back and surfaces a generic message (no traceback leak).
"""

import logging
import re

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from common.auth.db import db
from common.auth.models import User

PAGE_TYPES = {"portfolio", "ef", "compare", "benchmark"}
MIN_PASSWORD_LENGTH = 8
MAX_NAME_LENGTH = 100
GENERIC_DB_ERROR = "Something went wrong. Please try again."

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _commit() -> str | None:
    """Commit the session; on failure roll back and return a generic error message."""
    try:
        db.session.commit()
        return None
    except SQLAlchemyError:
        db.session.rollback()
        logging.exception("auth DB commit failed")
        return GENERIC_DB_ERROR


def create_user(email: str, password: str) -> tuple[User | None, str | None]:
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        return None, "Invalid email address."
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if db.session.scalar(db.select(User).filter_by(email=email)) is not None:
        return None, "This email is already registered."
    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    error = _commit()
    if error:
        return None, error
    return user, None


def verify_credentials(email: str, password: str) -> User | None:
    email = (email or "").strip().lower()
    user = db.session.scalar(db.select(User).filter_by(email=email))
    if user is None or not check_password_hash(user.password_hash, password or ""):
        return None
    return user

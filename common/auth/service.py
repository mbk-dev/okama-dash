"""Auth business logic as pure functions — unit-testable without Dash or a browser.

Callbacks are thin wrappers around these; every DB write goes through _commit()
so a failure rolls back and surfaces a generic message (no traceback leak).
"""

import logging
import re

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from common.auth.db import db
from common.auth.models import SavedConfig, User

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


def save_config(user_id: int, name: str, page_type: str, url: str) -> tuple[SavedConfig | None, str | None]:
    name = (name or "").strip()
    if not name:
        return None, "Name is required."
    if len(name) > MAX_NAME_LENGTH:
        return None, f"Name is too long (max {MAX_NAME_LENGTH} characters)."
    if page_type not in PAGE_TYPES:
        return None, "Unknown page type."
    if not (url or "").strip():
        return None, "Nothing to save yet — press Submit first."
    config = SavedConfig(user_id=user_id, name=name, page_type=page_type, url=url.strip())
    db.session.add(config)
    error = _commit()
    if error:
        return None, error
    return config, None


def list_configs(user_id: int) -> list[SavedConfig]:
    query = db.select(SavedConfig).filter_by(user_id=user_id).order_by(SavedConfig.id.desc())
    return list(db.session.scalars(query))


def _get_owned(user_id: int, config_id: int) -> SavedConfig | None:
    return db.session.scalar(db.select(SavedConfig).filter_by(id=config_id, user_id=user_id))


def rename_config(user_id: int, config_id: int, new_name: str) -> bool:
    new_name = (new_name or "").strip()
    if not new_name or len(new_name) > MAX_NAME_LENGTH:
        return False
    config = _get_owned(user_id, config_id)
    if config is None:
        return False
    config.name = new_name
    return _commit() is None


def delete_config(user_id: int, config_id: int) -> bool:
    config = _get_owned(user_id, config_id)
    if config is None:
        return False
    db.session.delete(config)
    return _commit() is None

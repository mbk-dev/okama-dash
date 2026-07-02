"""Request-context-safe wrappers around flask_login.current_user.

current_user raises outside a request context; these helpers degrade to
anonymous instead, so layout builders and tooling can call them anywhere.
"""

from flask import has_request_context
from flask_login import current_user


def user_is_authenticated() -> bool:
    return has_request_context() and bool(getattr(current_user, "is_authenticated", False))


def current_user_id() -> int | None:
    if not user_is_authenticated():
        return None
    return int(current_user.get_id())

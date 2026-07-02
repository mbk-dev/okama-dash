"""Flask-Login manager: session cookie -> User row."""

from flask_login import LoginManager

from common.auth.db import db
from common.auth.models import User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))

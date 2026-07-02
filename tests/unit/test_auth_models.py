import pytest
from sqlalchemy.exc import IntegrityError

from common.auth.db import db
from common.auth.models import SavedConfig, User

pytestmark = pytest.mark.unit


def test_user_and_config_roundtrip(auth_app):
    user = User(email="a@b.co", password_hash="x")
    db.session.add(user)
    db.session.commit()

    config = SavedConfig(user_id=user.id, name="My pf", page_type="portfolio", url="/portfolio?tickers=SPY.US")
    db.session.add(config)
    db.session.commit()

    stored = db.session.get(User, user.id)
    assert stored.email == "a@b.co"
    assert [c.name for c in stored.configs] == ["My pf"]
    assert stored.configs[0].created_at is not None


def test_user_email_must_be_unique(auth_app):
    db.session.add(User(email="a@b.co", password_hash="x"))
    db.session.commit()
    db.session.add(User(email="a@b.co", password_hash="y"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

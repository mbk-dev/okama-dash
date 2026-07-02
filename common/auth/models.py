"""User accounts and saved widget configurations."""

from flask_login import UserMixin

from common.auth.db import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    configs = db.relationship("SavedConfig", backref="user", lazy=True, cascade="all, delete-orphan")


class SavedConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    page_type = db.Column(db.String(20), nullable=False)  # portfolio | ef | compare | benchmark
    url = db.Column(db.Text, nullable=False)  # the shareable URL produced by create_link()
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

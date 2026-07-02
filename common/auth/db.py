"""Auth database binding — a single SQLAlchemy instance shared by models and services."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

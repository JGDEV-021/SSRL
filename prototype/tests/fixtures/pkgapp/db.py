""":mod:`pkgapp.db` — persistence layer for the test app."""
from . import models


def init_db():
    return "db-ready"


def save(item):
    return models.validate(item)
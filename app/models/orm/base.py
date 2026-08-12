"""Shared declarative base for all ORM-mapped tables.

Every ORM model (User, RefreshToken, and future ones) inherits from this
so that:
- Alembic can discover the full schema from one import root
  (target_metadata = Base.metadata in alembic/env.py)
- there's a single, unambiguous place that defines "this class maps to
  a table" for the whole app

This file should only ever be imported by files under app/models/orm/
and by Alembic's env.py — nothing in services, repositories (beyond
their own ORM imports), or routes should need it directly.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in this application."""
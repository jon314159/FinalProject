# app/database.py
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Common engine kwargs for reliability
_ENGINE_KW = dict(
    pool_pre_ping=True,          # drops dead connections before use
    pool_recycle=1800,           # recycle connections every 30 min
    pool_size=5,                 # tune to your app footprint
    max_overflow=10,
    pool_timeout=30,             # wait for a free conn before raising
)

# Add Postgres connect timeout if applicable
_connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith(("postgresql://", "postgres://")):
    # psycopg2 respects connect_timeout in seconds
    _connect_args["connect_timeout"] = 10

# Create the default engine and sessionmaker
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **_ENGINE_KW,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:  # pragma: no cover
    """
    One session per request. Always closes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Factory helpers (use same hardened defaults) ---

def get_engine(database_url: str = SQLALCHEMY_DATABASE_URL):
    """
    Create a new SQLAlchemy engine with hardened pool settings.
    """
    connect_args = {}
    if database_url.startswith(("postgresql://", "postgres://")):
        connect_args["connect_timeout"] = 10
    return create_engine(database_url, **_ENGINE_KW, connect_args=connect_args)

def get_sessionmaker(engine):
    """Factory to create a new sessionmaker bound to the given engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


# Optional: single retry helper for transient DB restarts
from sqlalchemy.exc import OperationalError, DisconnectionError  # noqa: E402

def retry_once_on_disconnect(fn):
    """
    Decorator to retry a DB action once if the pool has stale connections.
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (OperationalError, DisconnectionError):
            # Drop pool and try once more
            engine.dispose()
            return fn(*args, **kwargs)
    return wrapper

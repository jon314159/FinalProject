# app/database.py
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

def _normalize_database_url(database_url: str) -> str:
    """Normalize legacy provider URLs for SQLAlchemy 2.x."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _engine_options(database_url: str) -> dict:
    """Return safe engine options for PostgreSQL or SQLite."""
    if database_url.startswith("sqlite"):
        options = {"connect_args": {"check_same_thread": False}}
        if database_url.endswith(":memory:"):
            options["poolclass"] = StaticPool
        return options

    options = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
    }
    if database_url.startswith("postgresql://"):
        options["connect_args"] = {"connect_timeout": 10}
    return options

# Create the default engine and sessionmaker
engine = create_engine(
    _normalize_database_url(SQLALCHEMY_DATABASE_URL),
    **_engine_options(_normalize_database_url(SQLALCHEMY_DATABASE_URL)),
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
    normalized_url = _normalize_database_url(database_url)
    return create_engine(normalized_url, **_engine_options(normalized_url))

def get_sessionmaker(engine):
    """Factory to create a new sessionmaker bound to the given engine."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

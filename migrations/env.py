# migrations/env.py
from __future__ import annotations

import sys
from pathlib import Path
from logging.config import fileConfig
from typing import Optional, Literal
from sqlalchemy.schema import SchemaItem

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Ensure "app" package is importable (project root on sys.path)
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # folder that contains "app/" and "migrations/"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import your app config and metadata
from app.core.config import get_settings
from app.database import Base

# Alembic Config object, provides access to values in alembic.ini
config = context.config

# Configure logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at your models' metadata for autogenerate
target_metadata = Base.metadata

# Use the app's DATABASE_URL (overrides alembic.ini sqlalchemy.url)
settings = get_settings()
if getattr(settings, "DATABASE_URL", None):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def include_object(
    obj: SchemaItem,
    name: Optional[str],
    type_: Literal["schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"],
    reflected: bool,
    compare_to: Optional[SchemaItem],
) -> bool:
    # Example: skip Alembic's own version table (keep everything else)
    if type_ == "table" and name == "alembic_version":
        return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no Engine/DBAPI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        compare_type=True,            # detect type changes (e.g., VARCHAR(50)->255)
        compare_server_default=True,  # detect default changes
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with Engine/Connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enable batch mode automatically for SQLite (needed for ALTER COLUMN, etc.)
        render_as_batch = connection.dialect.name == "sqlite"

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

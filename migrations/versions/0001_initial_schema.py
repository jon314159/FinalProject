"""Create users and calculations tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Earlier releases created tables directly from SQLAlchemy metadata. The
    # checks below let Alembic adopt those existing development databases while
    # still creating the complete schema for new installations.
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("password", sa.String(length=255), nullable=False),
            sa.Column("first_name", sa.String(length=50), nullable=False),
            sa.Column("last_name", sa.String(length=50), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("is_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_id", "users", ["id"], unique=True)
        op.create_index("ix_users_username", "users", ["username"], unique=True)
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "calculations" not in existing_tables:
        op.create_table(
            "calculations",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column("inputs", sa.JSON(), nullable=False),
            sa.Column("result", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_calculations_type", "calculations", ["type"], unique=False)
        op.create_index("ix_calculations_user_id", "calculations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_calculations_user_id", table_name="calculations")
    op.drop_index("ix_calculations_type", table_name="calculations")
    op.drop_table("calculations")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

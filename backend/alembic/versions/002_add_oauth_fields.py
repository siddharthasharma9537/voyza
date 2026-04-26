"""Add OAuth fields to users table

Revision ID: 002_add_oauth_fields
Revises: 001_initial_schema
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_oauth_fields"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add OAuth provider support to users table."""
    # Add OAuth ID columns
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(255), unique=True, nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("apple_id", sa.String(255), unique=True, nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("facebook_id", sa.String(255), unique=True, nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(50), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false")
    )

    # Add indexes for OAuth IDs
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_apple_id", "users", ["apple_id"])
    op.create_index("ix_users_facebook_id", "users", ["facebook_id"])


def downgrade() -> None:
    """Revert OAuth field additions."""
    # Drop indexes
    op.drop_index("ix_users_facebook_id", "users")
    op.drop_index("ix_users_apple_id", "users")
    op.drop_index("ix_users_google_id", "users")

    # Drop columns
    op.drop_column("users", "email_verified")
    op.drop_column("users", "oauth_provider")
    op.drop_column("users", "facebook_id")
    op.drop_column("users", "apple_id")
    op.drop_column("users", "google_id")

"""Initial schema — all tables.

Revision ID: 001
Revises:
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("hashed_password", sa.VARCHAR(255), nullable=False),
        sa.Column("full_name", sa.VARCHAR(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.VARCHAR(255), nullable=False),
        sa.Column("slug", sa.VARCHAR(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # ------------------------------------------------------------------
    # memberships
    # ------------------------------------------------------------------
    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.VARCHAR(20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_memberships_user_org"),
    )
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_memberships_organization_id", "memberships", ["organization_id"])

    # ------------------------------------------------------------------
    # api_keys
    # ------------------------------------------------------------------
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("key_prefix", sa.VARCHAR(10), nullable=False),
        sa.Column("hashed_key", sa.VARCHAR(255), nullable=False),
        sa.Column("role", sa.VARCHAR(20), nullable=False, server_default="developer"),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_organization_id", "api_keys", ["organization_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # ------------------------------------------------------------------
    # sessions  (refresh token storage)
    # ------------------------------------------------------------------
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_token_hash", sa.VARCHAR(64), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("user_agent", sa.TEXT(), nullable=True),
        sa.Column("ip_address", sa.VARCHAR(45), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_refresh_token_hash", "sessions", ["refresh_token_hash"])

    # ------------------------------------------------------------------
    # requests  (inference log)
    # ------------------------------------------------------------------
    op.create_table(
        "requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.VARCHAR(50), nullable=False),
        sa.Column("model", sa.VARCHAR(100), nullable=False),
        sa.Column("routing_strategy", sa.VARCHAR(20), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.VARCHAR(20), nullable=False),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.Column("routing_decision", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt_hash", sa.VARCHAR(64), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_requests_user_id", "requests", ["user_id"])
    op.create_index("ix_requests_created_at", "requests", ["created_at"])
    op.create_index("ix_requests_provider", "requests", ["provider"])
    op.create_index("ix_requests_user_id_created_at", "requests", ["user_id", "created_at"])

    # ------------------------------------------------------------------
    # provider_status
    # ------------------------------------------------------------------
    op.create_table(
        "provider_status",
        sa.Column("provider", sa.VARCHAR(50), nullable=False),
        sa.Column("status", sa.VARCHAR(20), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("uptime_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("last_checked_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("error_message", sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint("provider"),
    )

    # ------------------------------------------------------------------
    # user_settings
    # ------------------------------------------------------------------
    op.create_table(
        "user_settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_routing_strategy", sa.VARCHAR(20), nullable=False, server_default="auto"),
        sa.Column("default_model", sa.VARCHAR(100), nullable=True),
        sa.Column("theme", sa.VARCHAR(10), nullable=False, server_default="dark"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("temperature", sa.Numeric(3, 2), nullable=False, server_default="0.70"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
    op.drop_table("provider_status")
    op.drop_index("ix_requests_user_id_created_at", table_name="requests")
    op.drop_index("ix_requests_provider", table_name="requests")
    op.drop_index("ix_requests_created_at", table_name="requests")
    op.drop_index("ix_requests_user_id", table_name="requests")
    op.drop_table("requests")
    op.drop_index("ix_sessions_refresh_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_api_keys_key_prefix", table_name="api_keys")
    op.drop_index("ix_api_keys_organization_id", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
    op.drop_table("users")

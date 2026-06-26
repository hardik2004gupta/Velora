"""Phase 4 — add request tracking columns to requests table.

Revision ID: 002
Revises: 001
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Human-readable request ID (req_xxxxxxxxxxxxxxxx)
    op.add_column("requests", sa.Column("request_id", sa.VARCHAR(24), nullable=True))
    # Conversation grouping
    op.add_column("requests", sa.Column("conversation_id", sa.VARCHAR(64), nullable=True))
    # Prompt and response text
    op.add_column("requests", sa.Column("prompt", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("response", sa.Text(), nullable=True))
    # Human-readable routing explanation (redundant with routing_decision JSONB
    # but kept as a plain-text column for fast display without JSON parsing)
    op.add_column("requests", sa.Column("routing_reason", sa.Text(), nullable=True))

    # Indexes
    op.create_index("ix_requests_request_id", "requests", ["request_id"], unique=True)
    op.create_index("ix_requests_conversation_id", "requests", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_requests_conversation_id", table_name="requests")
    op.drop_index("ix_requests_request_id", table_name="requests")
    op.drop_column("requests", "routing_reason")
    op.drop_column("requests", "response")
    op.drop_column("requests", "prompt")
    op.drop_column("requests", "conversation_id")
    op.drop_column("requests", "request_id")

"""Add delegation performance indexes for fast override path.

Revision ID: 002
Revises: 001
Create Date: 2025-08-17 18:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite index for fast override chain resolution
    op.create_index(
        "idx_active_delegations_lookup",
        "delegations",
        ["delegator_id", "is_deleted", "revoked_at", "poll_id", "mode", "created_at"],
        postgresql_where="is_deleted = false AND revoked_at IS NULL",
    )

    # Add index for delegatee lookups
    op.create_index(
        "idx_active_delegatee_lookup",
        "delegations",
        ["delegatee_id", "is_deleted", "revoked_at"],
        postgresql_where="is_deleted = false AND revoked_at IS NULL",
    )

    # Add index for chain origin tracking
    op.create_index(
        "idx_chain_origin_active",
        "delegations",
        ["chain_origin_id", "is_deleted", "revoked_at"],
        postgresql_where="is_deleted = false AND revoked_at IS NULL",
    )


def downgrade() -> None:
    # Remove performance indexes
    op.drop_index("idx_active_delegations_lookup", table_name="delegations")
    op.drop_index("idx_active_delegatee_lookup", table_name="delegations")
    op.drop_index("idx_chain_origin_active", table_name="delegations")

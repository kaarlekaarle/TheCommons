"""update delegations table

Revision ID: update_delegations_table
Revises: create_delegations_table
Create Date: 2025-08-11 16:25:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from backend.core.types import GUID

# revision identifiers, used by Alembic.
revision: str = "update_delegations_table"
down_revision: Union[str, None] = "create_delegations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing foreign key constraints
    op.drop_constraint("delegations_poll_id_fkey", "delegations", type_="foreignkey")
    op.drop_constraint("delegations_chain_origin_id_fkey", "delegations", type_="foreignkey")
    
    # Drop columns that are not needed for the new structure
    op.drop_column("delegations", "poll_id")
    op.drop_column("delegations", "revoked_at")
    op.drop_column("delegations", "chain_origin_id")
    op.drop_column("delegations", "start_date")
    op.drop_column("delegations", "end_date")
    
    # Rename delegatee_id to delegate_id
    op.alter_column("delegations", "delegatee_id", new_column_name="delegate_id")
    
    # Update the foreign key constraint name
    op.drop_constraint("delegations_delegatee_id_fkey", "delegations", type_="foreignkey")
    op.create_foreign_key(
        "delegations_delegate_id_fkey",
        "delegations", "users",
        ["delegate_id"], ["id"],
        ondelete="CASCADE"
    )
    
    # Add unique constraint to prevent multiple delegations per delegator
    op.create_unique_constraint(
        "uq_delegations_delegator", 
        "delegations", 
        ["delegator_id"]
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint("uq_delegations_delegator", "delegations", type_="unique")
    
    # Revert the foreign key constraint name
    op.drop_constraint("delegations_delegate_id_fkey", "delegations", type_="foreignkey")
    op.create_foreign_key(
        "delegations_delegatee_id_fkey",
        "delegations", "users",
        ["delegate_id"], ["id"]
    )
    
    # Rename delegate_id back to delegatee_id
    op.alter_column("delegations", "delegate_id", new_column_name="delegatee_id")
    
    # Add back the old columns
    op.add_column("delegations", sa.Column("poll_id", GUID(), nullable=True))
    op.add_column("delegations", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.add_column("delegations", sa.Column("chain_origin_id", GUID(), nullable=True))
    op.add_column("delegations", sa.Column("start_date", sa.DateTime(), nullable=False, server_default=sa.text("now()")))
    op.add_column("delegations", sa.Column("end_date", sa.DateTime(), nullable=True))
    
    # Recreate the old foreign key constraints
    op.create_foreign_key(
        "delegations_poll_id_fkey",
        "delegations", "polls",
        ["poll_id"], ["id"]
    )
    op.create_foreign_key(
        "delegations_chain_origin_id_fkey",
        "delegations", "users",
        ["chain_origin_id"], ["id"]
    )

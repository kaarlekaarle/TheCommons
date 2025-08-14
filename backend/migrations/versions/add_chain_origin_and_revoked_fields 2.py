"""add chain origin and revoked fields

Revision ID: add_chain_origin_and_revoked_fields
Revises: 151dde886663
Create Date: 2025-08-13 11:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_chain_origin_and_revoked_fields"
down_revision: Union[str, None] = "151dde886663"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing fields to delegations table
    with op.batch_alter_table("delegations") as batch_op:
        batch_op.add_column(sa.Column("chain_origin_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
        
        # Add foreign key constraint for chain_origin_id
        batch_op.create_foreign_key(
            "delegations_chain_origin_id_fkey",
            "users",
            ["chain_origin_id"], ["id"],
            ondelete="CASCADE"
        )


def downgrade() -> None:
    # Remove the fields
    with op.batch_alter_table("delegations") as batch_op:
        batch_op.drop_constraint("delegations_chain_origin_id_fkey", type_="foreignkey")
        batch_op.drop_column("revoked_at")
        batch_op.drop_column("chain_origin_id")

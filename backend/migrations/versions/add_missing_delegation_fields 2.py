"""add missing delegation fields

Revision ID: add_missing_delegation_fields
Revises: fix_delegation_field_naming
Create Date: 2025-08-13 11:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_missing_delegation_fields"
down_revision: Union[str, None] = "fix_delegation_field_naming"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing fields to delegations table
    with op.batch_alter_table("delegations") as batch_op:
        batch_op.add_column(sa.Column("poll_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("start_date", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
        batch_op.add_column(sa.Column("end_date", sa.DateTime(timezone=True), nullable=True))
        
        # Add foreign key constraint for poll_id
        batch_op.create_foreign_key(
            "delegations_poll_id_fkey",
            "polls",
            ["poll_id"], ["id"],
            ondelete="CASCADE"
        )


def downgrade() -> None:
    # Remove the fields
    with op.batch_alter_table("delegations") as batch_op:
        batch_op.drop_constraint("delegations_poll_id_fkey", type_="foreignkey")
        batch_op.drop_column("end_date")
        batch_op.drop_column("start_date")
        batch_op.drop_column("poll_id")

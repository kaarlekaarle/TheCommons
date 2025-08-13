"""fix delegation field naming

Revision ID: fix_delegation_field_naming
Revises: 12f2178ee94d
Create Date: 2025-08-13 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fix_delegation_field_naming"
down_revision: Union[str, None] = "12f2178ee94d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("delegations") as batch_op:
        # Rename delegate_id to delegatee_id for consistency
        batch_op.alter_column("delegate_id", new_column_name="delegatee_id")
        
        # Update the foreign key constraint name
        batch_op.drop_constraint("delegations_delegate_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "delegations_delegatee_id_fkey",
            "users",
            ["delegatee_id"], ["id"],
            ondelete="CASCADE"
        )


def downgrade() -> None:
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("delegations") as batch_op:
        # Revert the foreign key constraint name
        batch_op.drop_constraint("delegations_delegatee_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "delegations_delegate_id_fkey",
            "users",
            ["delegatee_id"], ["id"],
            ondelete="CASCADE"
        )
        
        # Rename delegatee_id back to delegate_id
        batch_op.alter_column("delegatee_id", new_column_name="delegate_id")

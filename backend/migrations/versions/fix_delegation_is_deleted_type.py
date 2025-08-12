"""fix delegation is_deleted type

Revision ID: fix_delegation_is_deleted_type
Revises: update_delegations_table
Create Date: 2025-08-11 16:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fix_delegation_is_deleted_type"
down_revision: Union[str, None] = "update_delegations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change is_deleted column from VARCHAR to BOOLEAN
    op.alter_column("delegations", "is_deleted",
                    existing_type=sa.String(),
                    type_=sa.Boolean(),
                    existing_nullable=True,
                    server_default=sa.text("false"))


def downgrade() -> None:
    # Change is_deleted column back to VARCHAR
    op.alter_column("delegations", "is_deleted",
                    existing_type=sa.Boolean(),
                    type_=sa.String(),
                    existing_nullable=True,
                    server_default=None)

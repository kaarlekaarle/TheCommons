"""create delegations table

Revision ID: create_delegations_table
Revises: add_unique_vote_constraint
Create Date: 2025-08-11 16:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from backend.core.types import GUID

# revision identifiers, used by Alembic.
revision: str = "create_delegations_table"
down_revision: Union[str, None] = "add_unique_vote_constraint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create delegations table
    op.create_table(
        "delegations",
        sa.Column("delegator_id", GUID(), nullable=False),
        sa.Column("delegate_id", GUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["delegate_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["delegator_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
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
    # Drop the delegations table
    op.drop_table("delegations")

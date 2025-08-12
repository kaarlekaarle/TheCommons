"""add unique vote constraint

Revision ID: add_unique_vote_constraint
Revises: 12f2178ee94d
Create Date: 2025-08-11 16:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_unique_vote_constraint"
down_revision: Union[str, None] = "12f2178ee94d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint to prevent multiple votes from same user on same poll
    op.create_unique_constraint(
        "uq_votes_user_poll", 
        "votes", 
        ["user_id", "poll_id"]
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint("uq_votes_user_poll", "votes", type_="unique")

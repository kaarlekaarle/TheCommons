"""add_unique_constraint_poll_labels_remove_duplicates

Revision ID: c46f3e8da2b5
Revises: add_labels_and_label_delegations
Create Date: 2025-08-14 10:13:17.115927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c46f3e8da2b5'
down_revision: Union[str, None] = 'add_labels_and_label_delegations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove duplicate poll-label relationships, keeping the first occurrence
    # For SQLite, we use ROWID to identify the first occurrence
    # For PostgreSQL, we would use CTID, but SQLite is our primary database
    
    # Delete duplicates keeping the minimum ROWID for each (poll_id, label_id) pair
    op.execute("""
        DELETE FROM poll_labels 
        WHERE ROWID NOT IN (
            SELECT MIN(ROWID) 
            FROM poll_labels 
            GROUP BY poll_id, label_id
        )
    """)
    
    # Add unique constraint on (poll_id, label_id)
    op.create_unique_constraint(
        'uq_poll_labels_poll_id_label_id', 
        'poll_labels', 
        ['poll_id', 'label_id']
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint(
        'uq_poll_labels_poll_id_label_id', 
        'poll_labels', 
        type_='unique'
    )
    # Note: We cannot restore duplicates that were deleted

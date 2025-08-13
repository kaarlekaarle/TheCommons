"""add_labels_and_label_delegations

Revision ID: add_labels_and_label_delegations
Revises: add_chain_origin_and_revoked_fields
Create Date: 2025-08-13 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from backend.core.types import GUID

# revision identifiers, used by Alembic.
revision: str = 'add_labels_and_label_delegations'
down_revision: Union[str, None] = 'add_chain_origin_and_revoked_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create labels table
    op.create_table('labels',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=40), nullable=False),
        sa.Column('slug', sa.String(length=40), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='idx_label_name_unique'),
        sa.UniqueConstraint('slug', name='idx_label_slug_unique')
    )
    
    # Create poll_labels association table
    op.create_table('poll_labels',
        sa.Column('poll_id', sa.String(length=32), nullable=False),
        sa.Column('label_id', sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['polls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['label_id'], ['labels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('poll_id', 'label_id')
    )
    
    # Add label_id column to delegations table
    op.add_column('delegations', sa.Column('label_id', sa.String(length=32), nullable=True))
    op.create_foreign_key(None, 'delegations', 'labels', ['label_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes
    op.create_index('idx_poll_labels_poll', 'poll_labels', ['poll_id'])
    op.create_index('idx_poll_labels_label', 'poll_labels', ['label_id'])
    op.create_index('idx_delegations_delegator_label', 'delegations', ['delegator_id', 'label_id'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_delegations_delegator_label', table_name='delegations')
    op.drop_index('idx_poll_labels_label', table_name='poll_labels')
    op.drop_index('idx_poll_labels_poll', table_name='poll_labels')
    
    # Drop foreign key and column
    op.drop_constraint(None, 'delegations', type_='foreignkey')
    op.drop_column('delegations', 'label_id')
    
    # Drop tables
    op.drop_table('poll_labels')
    op.drop_table('labels')

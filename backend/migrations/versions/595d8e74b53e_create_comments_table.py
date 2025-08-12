"""create_comments_table

Revision ID: 595d8e74b53e
Revises: fix_delegation_is_deleted_type
Create Date: 2025-08-11 18:25:50.730676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '595d8e74b53e'
down_revision: Union[str, None] = 'fix_delegation_is_deleted_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create comments table
    op.create_table('comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('poll_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['poll_id'], ['polls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_comments_poll_id_created_at', 'comments', ['poll_id', sa.text('created_at DESC')])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])
    op.create_index('ix_comments_is_deleted', 'comments', ['is_deleted'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_comments_is_deleted', table_name='comments')
    op.drop_index('ix_comments_user_id', table_name='comments')
    op.drop_index('ix_comments_poll_id_created_at', table_name='comments')
    
    # Drop comments table
    op.drop_table('comments')

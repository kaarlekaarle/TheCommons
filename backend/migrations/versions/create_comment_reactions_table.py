"""Create comment reactions table.

Revision ID: create_comment_reactions_table
Revises: 595d8e74b53e
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_comment_reactions_table'
down_revision = '595d8e74b53e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reaction type enum
    reaction_type_enum = postgresql.ENUM('up', 'down', name='reactiontype')
    reaction_type_enum.create(op.get_bind())
    
    # Create comment_reactions table
    op.create_table('comment_reactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('up', 'down', name='reactiontype'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_comment_reactions_comment_id'), 'comment_reactions', ['comment_id'], unique=False)
    op.create_index(op.f('ix_comment_reactions_user_id'), 'comment_reactions', ['user_id'], unique=False)
    
    # Create unique constraint
    op.create_unique_constraint('uq_comment_user_reaction', 'comment_reactions', ['comment_id', 'user_id'])


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_comment_user_reaction', 'comment_reactions', type_='unique')
    
    # Drop indexes
    op.drop_index(op.f('ix_comment_reactions_user_id'), table_name='comment_reactions')
    op.drop_index(op.f('ix_comment_reactions_comment_id'), table_name='comment_reactions')
    
    # Drop table
    op.drop_table('comment_reactions')
    
    # Drop enum
    reaction_type_enum = postgresql.ENUM('up', 'down', name='reactiontype')
    reaction_type_enum.drop(op.get_bind())

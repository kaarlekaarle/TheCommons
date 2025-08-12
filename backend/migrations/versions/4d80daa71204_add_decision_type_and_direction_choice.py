"""add_decision_type_and_direction_choice

Revision ID: 4d80daa71204
Revises: create_comment_reactions_table
Create Date: 2025-08-12 18:10:00.597936

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d80daa71204'
down_revision: Union[str, None] = 'create_comment_reactions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the decision_type enum
    decisiontype = sa.Enum("level_a", "level_b", name="decisiontype")
    decisiontype.create(op.get_bind(), checkfirst=True)
    
    # Add the decision_type column with default value
    op.add_column("polls", sa.Column("decision_type", decisiontype, nullable=False, server_default="level_b"))
    
    # Add the direction_choice column
    op.add_column("polls", sa.Column("direction_choice", sa.String(), nullable=True))


def downgrade() -> None:
    # Drop the direction_choice column
    op.drop_column("polls", "direction_choice")
    
    # Drop the decision_type column
    op.drop_column("polls", "decision_type")
    
    # Drop the enum
    sa.Enum(name="decisiontype").drop(op.get_bind(), checkfirst=True)

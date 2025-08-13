"""merge heads

Revision ID: 65028559b374
Revises: 4d80daa71204, fix_delegation_field_naming
Create Date: 2025-08-13 11:07:13.729734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65028559b374'
down_revision: Union[str, None] = ('4d80daa71204', 'fix_delegation_field_naming')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

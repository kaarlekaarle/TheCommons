"""merge heads

Revision ID: 151dde886663
Revises: 65028559b374, add_missing_delegation_fields
Create Date: 2025-08-13 11:10:09.764925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '151dde886663'
down_revision: Union[str, None] = ('65028559b374', 'add_missing_delegation_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

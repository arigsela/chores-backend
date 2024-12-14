"""add_chore_frequency

Revision ID: c2d2a79ffb04
Revises: c49bacd6cbab
Create Date: 2024-12-14 09:04:17.427000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d2a79ffb04'
down_revision: Union[str, None] = 'c49bacd6cbab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add frequency_per_week to chores table
    op.add_column('chores', sa.Column('frequency_per_week', sa.Integer(), nullable=False, server_default='1'))
    
    # Add occurrence_number to chore_assignments table
    op.add_column('chore_assignments', sa.Column('occurrence_number', sa.Integer(), nullable=False, server_default='1'))

def downgrade() -> None:
    # Remove the new columns
    op.drop_column('chores', 'frequency_per_week')
    op.drop_column('chore_assignments', 'occurrence_number')
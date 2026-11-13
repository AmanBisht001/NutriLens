"""add_monitored_nutrients_to_user_profiles

Revision ID: e5f2a1c8b301
Revises: d4e1f7a2b901
Create Date: 2026-11-11 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f2a1c8b301'
down_revision: Union[str, Sequence[str], None] = 'd4e1f7a2b901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_dietary_profiles',
        sa.Column('monitored_nutrients', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade() -> None:
    op.drop_column('user_dietary_profiles', 'monitored_nutrients')

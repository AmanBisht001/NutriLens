"""create_day8_food_journal_entries

Revision ID: f6a3b2d1c401
Revises: e5f2a1c8b301
Create Date: 2026-11-12 08:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a3b2d1c401'
down_revision: Union[str, Sequence[str], None] = 'e5f2a1c8b301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'food_journal_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('meal_type', sa.String(length=50), nullable=False, server_default='snack'),
        sa.Column('quantity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('serving_unit', sa.String(length=50), nullable=False, server_default='g'),
        sa.Column('serving_size_g', sa.Float(), nullable=True),
        sa.Column('total_weight_g', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_food_journal_entries_user_id'), 'food_journal_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_food_journal_entries_product_id'), 'food_journal_entries', ['product_id'], unique=False)
    op.create_index(op.f('ix_food_journal_entries_consumed_at'), 'food_journal_entries', ['consumed_at'], unique=False)
    op.create_index(op.f('ix_food_journal_entries_meal_type'), 'food_journal_entries', ['meal_type'], unique=False)
    op.create_index('ix_journal_user_consumed', 'food_journal_entries', ['user_id', 'consumed_at'], unique=False)
    op.create_index('ix_journal_user_meal', 'food_journal_entries', ['user_id', 'meal_type'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_journal_user_meal', table_name='food_journal_entries')
    op.drop_index('ix_journal_user_consumed', table_name='food_journal_entries')
    op.drop_index(op.f('ix_food_journal_entries_meal_type'), table_name='food_journal_entries')
    op.drop_index(op.f('ix_food_journal_entries_consumed_at'), table_name='food_journal_entries')
    op.drop_index(op.f('ix_food_journal_entries_product_id'), table_name='food_journal_entries')
    op.drop_index(op.f('ix_food_journal_entries_user_id'), table_name='food_journal_entries')
    op.drop_table('food_journal_entries')

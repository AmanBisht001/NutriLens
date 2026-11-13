"""create_day4_scan_tables

Revision ID: d4e1f7a2b901
Revises: 3e8e61f8d036
Create Date: 2026-11-11 20:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e1f7a2b901'
down_revision: Union[str, Sequence[str], None] = '3e8e61f8d036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_scans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='extracted'),
        sa.Column('images', sa.JSON(), nullable=False),
        sa.Column('raw_ocr_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('corrected_data', sa.JSON(), nullable=True),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_scans_user_id'), 'product_scans', ['user_id'], unique=False)
    op.create_index(op.f('ix_product_scans_product_id'), 'product_scans', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_scans_product_id'), table_name='product_scans')
    op.drop_index(op.f('ix_product_scans_user_id'), table_name='product_scans')
    op.drop_table('product_scans')

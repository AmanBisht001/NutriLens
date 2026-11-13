"""create_day9_admin_tables

Revision ID: a7b8c9d0e1f2
Revises: f6a3b2d1c401
Create Date: 2026-11-12 09:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a3b2d1c401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add role & is_admin to users
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='user'))
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # 2. Create scoring_rule_versions
    op.create_table(
        'scoring_rule_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('thresholds_food', sa.JSON(), nullable=False),
        sa.Column('thresholds_beverage', sa.JSON(), nullable=False),
        sa.Column('category_weights', sa.JSON(), nullable=False),
        sa.Column('general_weights', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scoring_rule_versions_version'), 'scoring_rule_versions', ['version'], unique=True)
    op.create_index(op.f('ix_scoring_rule_versions_is_active'), 'scoring_rule_versions', ['is_active'], unique=False)

    # 3. Create product_issues
    op.create_table(
        'product_issues',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('issue_type', sa.String(length=50), nullable=False, server_default='incorrect_nutrition'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proposed_correction', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_issues_product_id'), 'product_issues', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_issues_status'), 'product_issues', ['status'], unique=False)
    op.create_index(op.f('ix_product_issues_created_at'), 'product_issues', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_issues_created_at'), table_name='product_issues')
    op.drop_index(op.f('ix_product_issues_status'), table_name='product_issues')
    op.drop_index(op.f('ix_product_issues_product_id'), table_name='product_issues')
    op.drop_table('product_issues')

    op.drop_index(op.f('ix_scoring_rule_versions_is_active'), table_name='scoring_rule_versions')
    op.drop_index(op.f('ix_scoring_rule_versions_version'), table_name='scoring_rule_versions')
    op.drop_table('scoring_rule_versions')

    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'role')

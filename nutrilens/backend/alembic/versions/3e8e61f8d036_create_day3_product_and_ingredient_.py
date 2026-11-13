"""create_day3_product_and_ingredient_tables

Revision ID: 3e8e61f8d036
Revises: 
Create Date: 2026-11-11 19:13:55.386746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e8e61f8d036'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with Users, Profiles, Allergens, Ingredients, Products, and Nutrition Facts."""
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. user_dietary_profiles
    op.create_table(
        'user_dietary_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('dietary_preference', sa.String(length=100), nullable=False),
        sa.Column('allergies', sa.JSON(), nullable=False),
        sa.Column('dietary_restrictions', sa.JSON(), nullable=False),
        sa.Column('nutrition_goals', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_dietary_profiles_id'), 'user_dietary_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_user_dietary_profiles_user_id'), 'user_dietary_profiles', ['user_id'], unique=True)

    # 3. allergens
    op.create_table(
        'allergens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allergens_name'), 'allergens', ['name'], unique=True)
    op.create_index(op.f('ix_allergens_code'), 'allergens', ['code'], unique=False)

    # 4. ingredients
    op.create_table(
        'ingredients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('aliases', sa.Text(), nullable=True),
        sa.Column('purpose', sa.String(length=255), nullable=True),
        sa.Column('concern_level', sa.String(length=20), nullable=False, server_default='safe'),
        sa.Column('ins_number', sa.String(length=20), nullable=True),
        sa.Column('source_reference', sa.String(length=500), nullable=True),
        sa.Column('is_common_allergen', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingredients_name'), 'ingredients', ['name'], unique=False)
    op.create_index(op.f('ix_ingredients_normalized_name'), 'ingredients', ['normalized_name'], unique=True)
    op.create_index(op.f('ix_ingredients_category'), 'ingredients', ['category'], unique=False)
    op.create_index(op.f('ix_ingredients_ins_number'), 'ingredients', ['ins_number'], unique=False)
    op.create_index('ix_ingredient_category_concern', 'ingredients', ['category', 'concern_level'], unique=False)

    # 5. products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('brand', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('serving_size', sa.String(length=100), nullable=True),
        sa.Column('label_image_url', sa.String(length=500), nullable=True),
        sa.Column('raw_ingredients_text', sa.Text(), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=False, server_default='demo'),
        sa.Column('is_demo_data', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verification_note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_brand'), 'products', ['brand'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_barcode'), 'products', ['barcode'], unique=False)
    op.create_index('ix_product_name_brand', 'products', ['name', 'brand'], unique=False)
    op.create_index('ix_product_category_verified', 'products', ['category', 'is_verified'], unique=False)

    # 6. nutrition_facts
    op.create_table(
        'nutrition_facts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('energy_kcal', sa.Float(), nullable=True),
        sa.Column('total_fat_g', sa.Float(), nullable=True),
        sa.Column('saturated_fat_g', sa.Float(), nullable=True),
        sa.Column('trans_fat_g', sa.Float(), nullable=True),
        sa.Column('cholesterol_mg', sa.Float(), nullable=True),
        sa.Column('carbohydrates_g', sa.Float(), nullable=True),
        sa.Column('total_sugar_g', sa.Float(), nullable=True),
        sa.Column('added_sugar_g', sa.Float(), nullable=True),
        sa.Column('dietary_fibre_g', sa.Float(), nullable=True),
        sa.Column('protein_g', sa.Float(), nullable=True),
        sa.Column('sodium_mg', sa.Float(), nullable=True),
        sa.Column('calcium_mg', sa.Float(), nullable=True),
        sa.Column('iron_mg', sa.Float(), nullable=True),
        sa.Column('vitamin_c_mg', sa.Float(), nullable=True),
        sa.Column('serving_unit', sa.String(length=20), nullable=True, server_default='per_100g'),
        sa.Column('is_illustrative', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    op.create_index(op.f('ix_nutrition_facts_product_id'), 'nutrition_facts', ['product_id'], unique=True)

    # 7. product_ingredients
    op.create_table(
        'product_ingredients',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('ingredient_id', sa.String(length=36), nullable=False),
        sa.Column('original_text', sa.String(length=500), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'ingredient_id', name='uq_product_ingredient')
    )
    op.create_index(op.f('ix_product_ingredients_product_id'), 'product_ingredients', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_ingredients_ingredient_id'), 'product_ingredients', ['ingredient_id'], unique=False)

    # 8. product_allergens
    op.create_table(
        'product_allergens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('allergen_id', sa.String(length=36), nullable=False),
        sa.Column('declaration_type', sa.String(length=30), nullable=False, server_default='declared'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['allergen_id'], ['allergens.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'allergen_id', 'declaration_type', name='uq_product_allergen')
    )
    op.create_index(op.f('ix_product_allergens_product_id'), 'product_allergens', ['product_id'], unique=False)
    op.create_index(op.f('ix_product_allergens_allergen_id'), 'product_allergens', ['allergen_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('product_allergens')
    op.drop_table('product_ingredients')
    op.drop_table('nutrition_facts')
    op.drop_table('products')
    op.drop_table('ingredients')
    op.drop_table('allergens')
    op.drop_table('user_dietary_profiles')
    op.drop_table('users')

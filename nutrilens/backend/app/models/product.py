"""
NutriLens – Product & Ingredient Domain Models (Day 3)
Covers: Product, NutritionFacts, Ingredient, ProductIngredient, Allergen, ProductAllergen.
"""
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Allergen registry
# ---------------------------------------------------------------------------

class Allergen(Base):
    """Canonical allergen registry (peanuts, tree nuts, gluten, etc.)."""
    __tablename__ = "allergens"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(20), nullable=True, index=True)          # e.g. "EU_01" / "FDA_01"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product_allergens = relationship("ProductAllergen", back_populates="allergen")


# ---------------------------------------------------------------------------
# Ingredient registry
# ---------------------------------------------------------------------------

class Ingredient(Base):
    """
    Normalised ingredient knowledge-base entry.
    One canonical entry per ingredient; product uses it via ProductIngredient.
    """
    __tablename__ = "ingredients"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False, index=True)          # canonical display name
    normalized_name = Column(String(255), nullable=False, index=True, unique=True)  # lowercase, stripped
    category = Column(String(100), nullable=True, index=True)       # e.g. "preservative", "emulsifier"
    description = Column(Text, nullable=True)
    aliases = Column(Text, nullable=True)                           # JSON-encoded list stored as text
    purpose = Column(String(255), nullable=True)                    # e.g. "Extends shelf life"
    concern_level = Column(String(20), nullable=False, default="safe")  # safe | moderate | high
    ins_number = Column(String(20), nullable=True, index=True)      # E-number / INS code e.g. "E211"
    source_reference = Column(String(500), nullable=True)           # evidence URL or citation
    is_common_allergen = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product_ingredients = relationship("ProductIngredient", back_populates="ingredient")

    __table_args__ = (
        Index("ix_ingredient_category_concern", "category", "concern_level"),
    )


# ---------------------------------------------------------------------------
# Product catalogue
# ---------------------------------------------------------------------------

class Product(Base):
    """Core product record for a packaged food item."""
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(500), nullable=False, index=True)
    brand = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)       # e.g. "Biscuits & Cookies"
    barcode = Column(String(50), nullable=True, index=True)
    serving_size = Column(String(100), nullable=True)               # e.g. "30g" / "2 biscuits"
    label_image_url = Column(String(500), nullable=True)
    raw_ingredients_text = Column(Text, nullable=True)              # original label text
    data_source = Column(String(50), nullable=False, default="demo")
    # "demo" = seeded demo data | "scan" = OCR | "manual" = user-entered | "curated" = verified
    is_demo_data = Column(Boolean, default=False, nullable=False)   # clearly flags seed data
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    nutrition_facts = relationship(
        "NutritionFacts",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )
    product_ingredients = relationship(
        "ProductIngredient",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductIngredient.order_index",
        lazy="select",
    )
    product_allergens = relationship(
        "ProductAllergen",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_product_name_brand", "name", "brand"),
        Index("ix_product_category_verified", "category", "is_verified"),
    )


# ---------------------------------------------------------------------------
# Nutrition facts (1-to-1 with Product)
# ---------------------------------------------------------------------------

class NutritionFacts(Base):
    """
    Per-100g nutritional values for a product.
    All values are floats (nullable) to support partial data.
    NOTE: Demo data is clearly labelled illustrative; real data requires verification.
    """
    __tablename__ = "nutrition_facts"

    id = Column(String(36), primary_key=True, default=_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Macros – per 100g unless serving_unit specifies otherwise
    energy_kcal = Column(Float, nullable=True)
    total_fat_g = Column(Float, nullable=True)
    saturated_fat_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)
    carbohydrates_g = Column(Float, nullable=True)
    total_sugar_g = Column(Float, nullable=True)
    added_sugar_g = Column(Float, nullable=True)      # when separately declared on label
    dietary_fibre_g = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    # Micronutrients (optional)
    calcium_mg = Column(Float, nullable=True)
    iron_mg = Column(Float, nullable=True)
    vitamin_c_mg = Column(Float, nullable=True)
    # Metadata
    serving_unit = Column(String(20), nullable=True, default="per_100g")  # per_100g | per_serving
    is_illustrative = Column(Boolean, default=False, nullable=False)
    # True for demo/seed data – values are illustrative, not verified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="nutrition_facts")


# ---------------------------------------------------------------------------
# Product ↔ Ingredient association
# ---------------------------------------------------------------------------

class ProductIngredient(Base):
    """Junction table linking products to their resolved ingredient records."""
    __tablename__ = "product_ingredients"

    id = Column(String(36), primary_key=True, default=_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id = Column(
        String(36),
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    original_text = Column(String(500), nullable=True)   # raw text from OCR / label
    order_index = Column(Integer, nullable=False, default=0)  # position in ingredient list
    ocr_confidence = Column(Float, nullable=True)             # 0.0–1.0, None if manually entered
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")

    __table_args__ = (
        UniqueConstraint("product_id", "ingredient_id", name="uq_product_ingredient"),
        Index("ix_product_ingredient_product", "product_id"),
    )


# ---------------------------------------------------------------------------
# Product ↔ Allergen association
# ---------------------------------------------------------------------------

class ProductAllergen(Base):
    """Links allergens declared or suspected on a product label."""
    __tablename__ = "product_allergens"

    id = Column(String(36), primary_key=True, default=_uuid)
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allergen_id = Column(
        String(36),
        ForeignKey("allergens.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    declaration_type = Column(String(30), nullable=False, default="declared")
    # "declared" = "Contains: X" | "precautionary" = "May contain: X"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="product_allergens")
    allergen = relationship("Allergen", back_populates="product_allergens")

    __table_args__ = (
        UniqueConstraint("product_id", "allergen_id", "declaration_type", name="uq_product_allergen"),
    )

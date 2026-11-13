"""
Pydantic schemas for the product catalogue and ingredient knowledge base (Day 3).
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Allergen schemas
# ---------------------------------------------------------------------------

class AllergenResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductAllergenResponse(BaseModel):
    allergen: AllergenResponse
    declaration_type: str  # "declared" | "precautionary"

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Ingredient schemas
# ---------------------------------------------------------------------------

class IngredientBase(BaseModel):
    name: str
    normalized_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[str] = None      # JSON-encoded string
    purpose: Optional[str] = None
    concern_level: str = "safe"
    ins_number: Optional[str] = None
    source_reference: Optional[str] = None
    is_common_allergen: bool = False


class IngredientResponse(IngredientBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IngredientSummary(BaseModel):
    """Lightweight ingredient reference embedded in product detail."""
    id: str
    name: str
    category: Optional[str] = None
    concern_level: str = "safe"
    ins_number: Optional[str] = None
    purpose: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductIngredientResponse(BaseModel):
    """Ingredient line in a product's ingredient list."""
    ingredient: IngredientSummary
    original_text: Optional[str] = None
    order_index: int = 0
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Nutrition facts schemas
# ---------------------------------------------------------------------------

class NutritionFactsResponse(BaseModel):
    id: str
    energy_kcal: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    total_sugar_g: Optional[float] = None
    added_sugar_g: Optional[float] = None
    dietary_fibre_g: Optional[float] = None
    protein_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    serving_unit: Optional[str] = "per_100g"
    is_illustrative: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Product schemas
# ---------------------------------------------------------------------------

class ProductSummary(BaseModel):
    """Card-level product data for catalogue listings."""
    id: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: Optional[str] = None
    data_source: str = "demo"
    is_demo_data: bool = False
    is_verified: bool = False
    nutrition_facts: Optional[NutritionFactsResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductDetail(ProductSummary):
    """Full product detail including ingredients, allergens, and deterministic nutrition analysis."""
    raw_ingredients_text: Optional[str] = None
    label_image_url: Optional[str] = None
    verification_note: Optional[str] = None
    product_ingredients: List[ProductIngredientResponse] = []
    product_allergens: List[ProductAllergenResponse] = []
    nutrition_analysis: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Paginated list responses
# ---------------------------------------------------------------------------

class PaginatedProducts(BaseModel):
    items: List[ProductSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedIngredients(BaseModel):
    items: List[IngredientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Category list
# ---------------------------------------------------------------------------

class CategoryItem(BaseModel):
    name: str
    product_count: int


class CategoryListResponse(BaseModel):
    categories: List[CategoryItem]

"""
NutriLens – Administrative Schemas (Day 9)
Pydantic v2 schemas for admin operations:
- Dashboard statistics
- Product CRUD, verification, and ingredient/allergen mappings
- Canonical ingredient & allergen management
- Scoring rule version management
- User-reported data issues & corrections review
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Dashboard Statistics
# ---------------------------------------------------------------------------

class AdminDashboardStats(BaseModel):
    total_users: int
    total_products: int
    total_ingredients: int
    total_scans: int
    verified_products: int
    unverified_products: int
    total_issues: int
    pending_issues: int
    resolved_issues: int
    top_categories: List[Dict[str, Any]]
    active_scoring_rule_version: str


# ---------------------------------------------------------------------------
# 2. Product Management
# ---------------------------------------------------------------------------

class AdminIngredientMapping(BaseModel):
    ingredient_id: Optional[str] = None
    ingredient_name: Optional[str] = None
    order_index: int = 0
    percentage: Optional[float] = None


class AdminAllergenMapping(BaseModel):
    allergen_id: Optional[str] = None
    allergen_name: Optional[str] = None
    declaration_type: str = "declared"  # declared | precautionary


class AdminNutritionFactsPayload(BaseModel):
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


class AdminProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: Optional[str] = None
    label_image_url: Optional[str] = None
    raw_ingredients_text: Optional[str] = None
    is_verified: bool = False
    verification_note: Optional[str] = None
    nutrition_facts: Optional[AdminNutritionFactsPayload] = None
    ingredient_mappings: Optional[List[AdminIngredientMapping]] = None
    allergen_mappings: Optional[List[AdminAllergenMapping]] = None


class AdminProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    serving_size: Optional[str] = None
    label_image_url: Optional[str] = None
    raw_ingredients_text: Optional[str] = None
    is_verified: Optional[bool] = None
    verification_note: Optional[str] = None
    nutrition_facts: Optional[AdminNutritionFactsPayload] = None
    ingredient_mappings: Optional[List[AdminIngredientMapping]] = None
    allergen_mappings: Optional[List[AdminAllergenMapping]] = None


class AdminProductVerifyPayload(BaseModel):
    is_verified: bool
    verification_note: Optional[str] = None


# ---------------------------------------------------------------------------
# 3. Ingredient & Allergen Management
# ---------------------------------------------------------------------------

class AdminIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    normalized_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = Field(default_factory=list)
    purpose: Optional[str] = None
    concern_level: str = "safe"  # safe | moderate | high
    ins_number: Optional[str] = None
    source_reference: Optional[str] = None
    is_common_allergen: bool = False


class AdminIngredientUpdate(BaseModel):
    name: Optional[str] = None
    normalized_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    purpose: Optional[str] = None
    concern_level: Optional[str] = None
    ins_number: Optional[str] = None
    source_reference: Optional[str] = None
    is_common_allergen: Optional[bool] = None


class AdminAllergenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None
    description: Optional[str] = None


class AdminAllergenUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# 4. Scoring Rule Version Management
# ---------------------------------------------------------------------------

class ScoringRuleVersionCreate(BaseModel):
    version: str = Field(..., min_length=1, max_length=50, description="Unique version key e.g. nutrilens-score-v1.1")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = False
    thresholds_food: Optional[Dict[str, Any]] = None
    thresholds_beverage: Optional[Dict[str, Any]] = None
    category_weights: Optional[Dict[str, Any]] = None
    general_weights: Optional[Dict[str, Any]] = None


class ScoringRuleVersionResponse(BaseModel):
    id: str
    version: str
    name: str
    description: Optional[str] = None
    is_active: bool
    thresholds_food: Dict[str, Any]
    thresholds_beverage: Dict[str, Any]
    category_weights: Dict[str, Any]
    general_weights: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 5. User-Reported Issues Management
# ---------------------------------------------------------------------------

class ProductIssueCreate(BaseModel):
    product_id: str
    issue_type: str = "incorrect_nutrition"  # incorrect_nutrition | missing_ingredient | wrong_allergen | bad_category | other
    description: str = Field(..., min_length=5, max_length=2000)
    proposed_correction: Optional[Dict[str, Any]] = None


class ProductIssueUpdate(BaseModel):
    status: str = Field(..., description="pending | reviewed | resolved | dismissed")
    admin_notes: Optional[str] = None


class ProductIssueResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    product_id: str
    product_name: str
    product_brand: Optional[str] = None
    issue_type: str
    description: str
    proposed_correction: Optional[Dict[str, Any]] = None
    status: str
    admin_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

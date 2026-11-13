"""
NutriLens – Product Comparison & Alternative Recommendation Schemas (Day 7)
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.schemas.user import DietaryPreferencesPayload


VALID_PRIORITIES = [
    "lower_sugar",
    "lower_sodium",
    "lower_saturated_fat",
    "higher_protein",
    "higher_fibre",
    "fewer_restriction_conflicts",
]


class ComparisonRequest(BaseModel):
    product_ids: List[str] = Field(
        ...,
        min_length=2,
        max_length=6,
        description="List of 2 to 6 product IDs to compare",
    )
    priorities: Optional[List[str]] = Field(
        default=None,
        description="Optional list of user comparison priorities: lower_sugar, lower_sodium, lower_saturated_fat, higher_protein, higher_fibre, fewer_restriction_conflicts",
    )
    user_preferences: Optional[DietaryPreferencesPayload] = Field(
        default=None,
        description="Optional dietary preferences override; falls back to authenticated user profile if omitted",
    )


class ProductComparisonItem(BaseModel):
    product_id: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[str] = None
    label_image_url: Optional[str] = None
    standard_unit: str = "per_100g"
    score: Optional[int] = None
    grade: Optional[str] = None
    rating_label: Optional[str] = None
    rating_color: Optional[str] = None
    data_completeness_pct: float = 0.0
    nutrients_per_100: Dict[str, Optional[float]]
    nutrients_per_serving: Dict[str, Optional[float]]
    missing_nutrients: List[str] = []
    ingredients: List[str] = []
    allergens_declared: List[str] = []
    allergens_precautionary: List[str] = []
    suitability_status: str
    suitability_badge: str
    suitability_conflicts: List[str] = []
    price: Optional[float] = None
    price_display: str = "Not declared"


class PriorityRanking(BaseModel):
    product_id: str
    product_name: str
    value: Optional[float] = None
    unit: str = ""
    rank: int
    note: str


class PriorityEvaluationItem(BaseModel):
    priority: str
    priority_label: str
    best_product_id: Optional[str] = None
    best_product_name: Optional[str] = None
    summary: str
    rankings: List[PriorityRanking] = []


class ComparisonMatrixResponse(BaseModel):
    products: List[ProductComparisonItem]
    common_ingredients: List[str] = []
    common_allergens: List[str] = []
    priorities_evaluated: List[str] = []
    priority_evaluations: List[PriorityEvaluationItem] = []
    summary: str


class AlternativeRecommendationItem(BaseModel):
    product_id: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[str] = None
    label_image_url: Optional[str] = None
    score: Optional[int] = None
    grade: Optional[str] = None
    rating_label: Optional[str] = None
    rating_color: Optional[str] = None
    suitability_status: str
    suitability_badge: str
    match_score: float
    reasons: List[str] = []
    nutritional_advantages: List[str] = []
    nutrients_per_100: Dict[str, Optional[float]]
    missing_nutrients: List[str] = []


class ProductAlternativesResponse(BaseModel):
    target_product_id: str
    target_product_name: str
    target_category: Optional[str] = None
    target_score: Optional[int] = None
    applied_priorities: List[str] = []
    total_candidates_evaluated: int
    alternatives: List[AlternativeRecommendationItem]

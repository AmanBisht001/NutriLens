"""
NutriLens – Scoring Engine Pydantic Schemas (Day 5)
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ServingSizeInfo(BaseModel):
    raw_text: Optional[str] = None
    quantity: Optional[float] = None
    unit: str = "g"
    standard_reference: str = "100g"


class FactorItem(BaseModel):
    factor: str
    impact: str
    severity: Optional[str] = None
    description: str


class ScoreBreakdown(BaseModel):
    base_score: float
    total_penalties: float
    total_bonuses: float
    penalties: Dict[str, float] = Field(default_factory=dict)
    bonuses: Dict[str, float] = Field(default_factory=dict)
    category_used: str


class NutritionAnalysisResponse(BaseModel):
    status: str = Field(..., description="'complete' or 'insufficient_data'")
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    score: Optional[int] = Field(None, ge=0, le=100, description="NutriLens Nutrition Score (0-100)")
    grade: Optional[str] = Field(None, description="Letter grade A, B, C, D, E")
    rating_label: str
    rating_color: str
    standard_unit: str = "per_100g"
    per_100_values: Dict[str, Optional[float]] = Field(default_factory=dict)
    per_serving_values: Dict[str, Optional[float]] = Field(default_factory=dict)
    serving_size_info: Dict[str, Any] = Field(default_factory=dict)
    data_completeness_pct: float
    missing_critical_fields: List[str] = Field(default_factory=list)
    missing_optional_fields: List[str] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    nutrition_summary: str
    score_explanation: str
    positive_factors: List[Dict[str, Any]] = Field(default_factory=list)
    attention_factors: List[Dict[str, Any]] = Field(default_factory=list)
    nutrient_evaluations: Dict[str, Any] = Field(default_factory=dict)
    score_breakdown: Optional[Dict[str, Any]] = None
    scoring_rule_version: str
    disclaimer: str


class CustomScoreRequest(BaseModel):
    nutrients: Dict[str, Optional[float]] = Field(
        ...,
        description="Per-100g/ml nutrient values: energy_kcal, total_fat_g, saturated_fat_g, carbohydrates_g, total_sugar_g, protein_g, sodium_mg, etc."
    )
    category: Optional[str] = "General"
    serving_size: Optional[str] = "100g"

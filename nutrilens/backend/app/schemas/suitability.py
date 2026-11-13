"""
NutriLens – Suitability Pydantic Schemas (Day 6)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SuitabilityRequest(BaseModel):
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    nutrition_goals: Optional[List[str]] = None
    monitored_nutrients: Optional[List[str]] = None


class SuitabilityConflictItem(BaseModel):
    category: str
    severity: str
    title: str
    detail: str
    source_ingredient: Optional[str] = None
    is_precautionary: bool = False


class SuitabilityResponse(BaseModel):
    status: str = Field(
        ...,
        description="'Suitable based on available information', 'Caution', 'Declared restriction conflict', or 'Insufficient information'",
    )
    status_label: str
    badge_color: str
    is_suitable: bool
    product_id: str
    product_name: str
    summary_narrative: str
    evaluated_preferences: Dict[str, Any]
    conflicts: List[SuitabilityConflictItem] = Field(default_factory=list)
    cautions: List[SuitabilityConflictItem] = Field(default_factory=list)
    positive_observations: List[Dict[str, Any]] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    rules_applied: List[str] = Field(default_factory=list)
    engine_version: str
    disclaimer: str

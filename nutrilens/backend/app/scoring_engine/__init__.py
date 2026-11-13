"""
NutriLens – Scoring Engine Package (Day 5)
Deterministic nutrition analysis and scoring system.
"""
from app.scoring_engine.rules import SCORING_RULE_VERSION, CATEGORY_RULES
from app.scoring_engine.validators import validate_nutrition_data, NutritionValidationResult
from app.scoring_engine.calculator import (
    parse_serving_size,
    calculate_serving_values,
    calculate_deterministic_score,
)
from app.scoring_engine.explanations import (
    evaluate_individual_nutrients,
    build_factors_and_narratives,
    DISCLAIMER_TEXT,
)
from app.scoring_engine.service import (
    analyze_nutrition_payload,
    analyze_product_by_id,
)

__all__ = [
    "SCORING_RULE_VERSION",
    "CATEGORY_RULES",
    "validate_nutrition_data",
    "NutritionValidationResult",
    "parse_serving_size",
    "calculate_serving_values",
    "calculate_deterministic_score",
    "evaluate_individual_nutrients",
    "build_factors_and_narratives",
    "DISCLAIMER_TEXT",
    "analyze_nutrition_payload",
    "analyze_product_by_id",
]

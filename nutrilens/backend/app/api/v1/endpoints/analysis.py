"""
NutriLens – Nutrition Analysis & Scoring Endpoints (Day 5)
Handles:
- GET /api/products/{id}/analysis
- POST /api/analysis/score
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.scoring import NutritionAnalysisResponse, CustomScoreRequest
from app.scoring_engine.service import (
    analyze_product_by_id,
    analyze_nutrition_payload,
)

router = APIRouter()


@router.get(
    "/products/{product_id}/analysis",
    response_model=NutritionAnalysisResponse,
    summary="Compute deterministic NutriLens nutrition analysis for a catalogue product",
)
def get_product_nutrition_analysis(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns the deterministic NutriLens Nutrition Score (0-100),
    positive/negative factors, per-100g and per-serving breakdowns,
    nutrient evaluations, and transparency explanations.
    """
    analysis = analyze_product_by_id(product_id, db)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' was not found.",
        )
    return analysis


@router.post(
    "/analysis/score",
    response_model=NutritionAnalysisResponse,
    summary="Calculate deterministic nutrition score for arbitrary nutritional values",
)
def calculate_custom_nutrition_score(
    payload: CustomScoreRequest,
):
    """
    Calculates deterministic NutriLens score and explanations for custom nutritional inputs
    (e.g. food scan review preview, user what-if scenarios).
    """
    return analyze_nutrition_payload(
        nutrients_per_100=payload.nutrients,
        category=payload.category,
        serving_size_str=payload.serving_size,
    )

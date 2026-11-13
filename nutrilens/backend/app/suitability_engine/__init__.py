"""
NutriLens – Suitability Engine Package (Day 6)
Personalized dietary suitability evaluation.
"""
from app.suitability_engine.rules import (
    SUITABILITY_ENGINE_VERSION,
    STATUS_SUITABLE,
    STATUS_CAUTION,
    STATUS_CONFLICT,
    STATUS_INSUFFICIENT,
    SAFETY_DISCLAIMER,
)
from app.suitability_engine.matcher import evaluate_suitability
from app.suitability_engine.service import (
    evaluate_product_suitability,
    get_user_dietary_profile,
    update_user_dietary_profile,
)

__all__ = [
    "SUITABILITY_ENGINE_VERSION",
    "STATUS_SUITABLE",
    "STATUS_CAUTION",
    "STATUS_CONFLICT",
    "STATUS_INSUFFICIENT",
    "SAFETY_DISCLAIMER",
    "evaluate_suitability",
    "evaluate_product_suitability",
    "get_user_dietary_profile",
    "update_user_dietary_profile",
]

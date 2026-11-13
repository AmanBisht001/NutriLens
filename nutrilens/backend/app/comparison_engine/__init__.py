"""
NutriLens – Comparison Engine Package (Day 7)
"""
from app.comparison_engine.comparator import compare_products
from app.comparison_engine.recommendations import get_alternative_recommendations

__all__ = [
    "compare_products",
    "get_alternative_recommendations",
]
